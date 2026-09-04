#!/usr/bin/env python
"""
rnadisease_to_kgx.py: Ingests RNADisease v4.0 into Biolink-compliant KGX format.

Parses experimentally supported human RNA-disease associations (miRNA, lncRNA, circRNA, etc.),
maps diseases strictly to canonical MONDO CURIEs via DO ID, MeSH ID, labels, and synonyms,
maps RNAs strictly to canonical RNACENTRAL:URS... CURIEs (zero synthetic fallbacks),
and produces strongly-typed KGX TSVs linking biolink:RNAProduct directly to biolink:Disease.
"""

import argparse
import csv
import gzip
import json
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple


def parse_args():
    parser = argparse.ArgumentParser(
        prog="rnadisease_to_kgx.py",
        description="Transform RNADisease v4.0 into KGX format with strict Biolink CURIEs.",
    )
    parser.add_argument("-i", "--input", required=True, help="Path to RNADisease raw file (.xlsx, .tsv, or .tsv.gz).")
    parser.add_argument("-m", "--mondo-json", default="../data/raw/mondo.json", help="Path to mondo.json.")
    parser.add_argument("-r", "--rnamapping", default=None, help="Path to RNAcentral tarbase miRNA mapping TSV.")
    parser.add_argument("-e", "--ensemblmapping", default=None, help="Path to RNAcentral ensembl mapping TSV.")
    parser.add_argument("-n", "--noncodemapping", default=None, help="Path to RNAcentral noncode mapping TSV.")
    parser.add_argument("-g", "--genes", default=None, help="Path to ensembl_genes.csv.")
    parser.add_argument("-v", "--version", default="4.0", help="RNADisease database release version.")
    parser.add_argument("-o", "--output", nargs=2, required=True, help="Output paths for nodes.tsv and edges.tsv.")
    return parser.parse_args()


# Curated high-frequency MeSH ontology mappings to MONDO
MESH_DIRECT_MAP = {
    "breast neoplasms": "MONDO:0007254",            # breast cancer
    "colorectal neoplasms": "MONDO:0005575",        # colorectal cancer
    "stomach neoplasms": "MONDO:0001056",           # gastric cancer
    "prostatic neoplasms": "MONDO:0008315",         # prostate cancer
    "uterine cervical neoplasms": "MONDO:0002974",  # cervical cancer
    "ovarian neoplasms": "MONDO:0008170",           # ovarian cancer
    "diabetic nephropathies": "MONDO:0005015",      # diabetic kidney disease
    "triple negative breast neoplasms": "MONDO:0005477", # triple-negative breast cancer
    "colonic neoplasms": "MONDO:0002271",           # colon cancer
    "carcinoma, non-small-cell lung": "MONDO:0005233", # non-small cell lung carcinoma
    "sepsis": "MONDO:0005327",                      # sepsis
    "inflammation": "MONDO:0021151",                # inflammatory disease
    "fibrosis": "MONDO:0004975",                    # fibrosis
    "cardiomegaly": "MONDO:0005003",                # cardiomegaly
    "ischemic stroke": "MONDO:0005110",             # ischemic stroke
    "spinal cord injuries": "MONDO:0005500",        # spinal cord injury
    "myocardial reperfusion injury": "MONDO:0006764",
    "cardiovascular diseases": "MONDO:0004995",     # cardiovascular disease
    "inflammatory bowel diseases": "MONDO:0005265", # inflammatory bowel disease
    "carcinoma, ovarian epithelial": "MONDO:0008170",
    "hepatitis c": "MONDO:0005151",                 # hepatitis C
    "precursor cell lymphoblastic leukemia-lymphoma": "MONDO:0004966",
    "psoriasis 1": "MONDO:0008323",
    "reperfusion injury": "MONDO:0006764",
}


def load_mondo_indexes(mondo_json_path: str) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """
    Builds lookup tables from DOID xrefs, MeSH xrefs, and disease names/synonyms to MONDO CURIEs.
    """
    doid_to_mondo = {}
    mesh_to_mondo = {}
    name_to_mondo = {}

    if not os.path.exists(mondo_json_path):
        print(f"Warning: {mondo_json_path} not found. Skipping MONDO index.")
        return doid_to_mondo, mesh_to_mondo, name_to_mondo

    with open(mondo_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for graph in data.get("graphs", []):
            for node in graph.get("nodes", []):
                nid = node.get("id", "")
                if "/MONDO_" in nid:
                    curie = "MONDO:" + nid.split("/MONDO_")[-1]
                    lbl = node.get("lbl", "")
                    if lbl:
                        s = lbl.strip().lower()
                        name_to_mondo[s] = curie
                        name_to_mondo[s.replace("-", " ")] = curie
                    for syn in node.get("meta", {}).get("synonyms", []):
                        val = syn.get("val", "")
                        if val:
                            s = val.strip().lower()
                            name_to_mondo[s] = curie
                            name_to_mondo[s.replace("-", " ")] = curie
                    for xref in node.get("meta", {}).get("xrefs", []):
                        val = xref.get("val", "")
                        if val.startswith("DOID:"):
                            doid_to_mondo[val] = curie
                        elif val.startswith("MESH:"):
                            mesh_to_mondo[val.replace("MESH:", "")] = curie

    return doid_to_mondo, mesh_to_mondo, name_to_mondo


def match_disease_to_mondo(
    doid: str,
    mesh_id: str,
    disease_name: str,
    doid_index: Dict[str, str],
    mesh_index: Dict[str, str],
    name_index: Dict[str, str],
) -> Optional[str]:
    """
    Resolves disease to canonical MONDO CURIE via DO ID, MeSH ID, or Name / Synonyms.
    """
    # 1. Primary: DO ID cross-reference
    if doid and doid in doid_index:
        return doid_index[doid]

    # 2. Secondary: MeSH ID cross-reference
    clean_mesh = mesh_id.replace("MESH:", "").strip()
    if clean_mesh and clean_mesh in mesh_index:
        return mesh_index[clean_mesh]

    # 3. Tertiary: Curated direct MeSH mapping & exact name match
    s = disease_name.strip().lower()
    if s in MESH_DIRECT_MAP:
        return MESH_DIRECT_MAP[s]
    if s in name_index:
        return name_index[s]

    s_clean = s.replace("-", " ")
    if s_clean in name_index:
        return name_index[s_clean]

    # 4. Plural / terminology normalization
    plural_patterns = [
        (r"\bneoplasms\b", "neoplasm"),
        (r"\bneoplasms\b", "cancer"),
        (r"\bdiseases\b", "disease"),
        (r"\binjuries\b", "injury"),
    ]
    for pat, rep in plural_patterns:
        cand = re.sub(pat, rep, s_clean)
        if cand in name_index:
            return name_index[cand]

    # 5. Inverted MeSH syntax: "Carcinoma, Hepatocellular" -> "hepatocellular carcinoma"
    if "," in s:
        parts = [p.strip() for p in s.split(",")]
        rev = " ".join(reversed(parts))
        rev_clean = rev.replace("-", " ")
        if rev in name_index:
            return name_index[rev]
        if rev_clean in name_index:
            return name_index[rev_clean]
        for pat, rep in plural_patterns:
            cand = re.sub(pat, rep, rev_clean)
            if cand in name_index:
                return name_index[cand]

    return None


def load_rna_indexes(
    tarbase_path: Optional[str],
    ensembl_path: Optional[str],
    noncode_path: Optional[str],
    genes_path: Optional[str],
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, str]]:
    """
    Loads RNAcentral mapping indexes for miRNAs, Ensembl lncRNAs, NONCODE lncRNAs, and Gene Symbols.
    """
    mir_to_urs: Dict[str, str] = {}
    if tarbase_path and os.path.exists(tarbase_path):
        with open(tarbase_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    urs = parts[0].strip()
                    mir_name = parts[2].strip().lower()
                    mir_to_urs[mir_name] = f"RNACENTRAL:{urs}"
                    stem = re.sub(r"-[53]p$", "", mir_name)
                    if stem not in mir_to_urs:
                        mir_to_urs[stem] = f"RNACENTRAL:{urs}"

    ensg_to_urs: Dict[str, str] = {}
    if ensembl_path and os.path.exists(ensembl_path):
        with open(ensembl_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 6:
                    urs = parts[0].strip()
                    ensg = parts[5].strip().split(".")[0]
                    if ensg not in ensg_to_urs:
                        ensg_to_urs[ensg] = f"RNACENTRAL:{urs}"

    noncode_to_urs: Dict[str, str] = {}
    if noncode_path and os.path.exists(noncode_path):
        with open(noncode_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 6:
                    urs = parts[0].strip()
                    t_id = parts[2].strip().upper()
                    g_id = parts[5].strip().upper()
                    if t_id not in noncode_to_urs:
                        noncode_to_urs[t_id] = f"RNACENTRAL:{urs}"
                    if g_id not in noncode_to_urs:
                        noncode_to_urs[g_id] = f"RNACENTRAL:{urs}"

    symbol_to_ensg: Dict[str, str] = {}
    if genes_path and os.path.exists(genes_path):
        with open(genes_path, "r", encoding="utf-8") as f:
            for line in f:
                m_id = re.search(r'gene_id\s+"([^"]+)"', line)
                m_name = re.search(r'gene_name\s+"([^"]+)"', line)
                if m_id and m_name:
                    symbol_to_ensg[m_name.group(1).strip().upper()] = m_id.group(1).strip().split(".")[0]

    return mir_to_urs, ensg_to_urs, noncode_to_urs, symbol_to_ensg


def match_rna_to_rnacentral(
    symbol: str,
    rna_type: str,
    mir_index: Dict[str, str],
    ensg_index: Dict[str, str],
    noncode_index: Dict[str, str],
    symbol_to_ensg: Dict[str, str],
) -> Optional[str]:
    """
    Grounds RNA symbol to canonical RNACENTRAL:URS... CURIE without synthetic fallbacks.
    """
    sym = symbol.strip()
    sym_l = sym.lower()
    sym_u = sym.upper()

    # 1. MicroRNAs
    if rna_type == "miRNA" or "mir" in sym_l or "let-" in sym_l:
        # Exact mature or stem
        urs = mir_index.get(sym_l) or mir_index.get(re.sub(r"-[53]p$", "", sym_l))
        if not urs:
            # Strip precursor locus number: hsa-let-7a-1 -> hsa-let-7a
            locus_strip = re.sub(r"-\d+$", "", sym_l)
            urs = mir_index.get(locus_strip)
        if not urs:
            # Modern miRBase suffix letter re-annotations: hsa-miR-203 -> hsa-miR-203a-3p
            urs = (
                mir_index.get(sym_l + "a")
                or mir_index.get(sym_l + "a-3p")
                or mir_index.get(sym_l + "a-5p")
            )
        if not urs and "-" in sym_l:
            locus_strip = re.sub(r"-\d+$", "", sym_l)
            urs = mir_index.get(locus_strip + "a")
        if urs:
            return urs

    # 2. lncRNAs & Other RNAs
    # Gene symbol -> ENSG -> URS
    ensg = symbol_to_ensg.get(sym_u)
    if ensg and ensg in ensg_index:
        return ensg_index[ensg]

    # NONCODE accession
    if sym_u in noncode_index:
        return noncode_index[sym_u]

    # Direct ENSG in symbol
    if sym_u in ensg_index:
        return ensg_index[sym_u]

    # Fallback to miRNA index in case type was ambiguously labeled
    if sym_l in mir_index:
        return mir_index[sym_l]

    return None


def iter_rnadisease_rows(input_path: str):
    """
    Yields rows from .xlsx, .tsv.gz, or .tsv file.
    Row structure: (RDID, specise, RNA Symbol, RNA Type, Disease Name, DO ID, MeSH ID, KEGG disease ID, PMID, score)
    """
    if input_path.endswith(".xlsx"):
        import openpyxl

        wb = openpyxl.load_workbook(input_path, read_only=True)
        ws = wb.active
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                continue
            yield ["" if c is None else str(c).strip() for c in row]
    else:
        open_fn = gzip.open if input_path.endswith(".gz") else open
        with open_fn(input_path, "rt", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader, None)
            for row in reader:
                yield [c.strip() for c in row]


def process_rnadisease(
    input_path: str,
    mondo_json: str,
    rnamapping: Optional[str],
    ensemblmapping: Optional[str],
    noncodemapping: Optional[str],
    genes: Optional[str],
    version: str,
    nodes_path: str,
    edges_path: str,
):
    """
    Parses RNADisease records and outputs strictly compliant Biolink nodes and edges.
    Enforces pure Unix line endings and canonical Biolink CURIEs.
    """
    print(f"Loading MONDO ontology indexes from: {mondo_json}")
    doid_index, mesh_index, name_index = load_mondo_indexes(mondo_json)

    print("Loading RNAcentral mapping indexes...")
    mir_index, ensg_index, noncode_index, symbol_to_ensg = load_rna_indexes(
        rnamapping, ensemblmapping, noncodemapping, genes
    )

    nodes: Dict[str, Dict[str, str]] = {}
    edges: List[Dict[str, str]] = []
    seen_edges: Set[Tuple[str, str, str, str]] = set()

    total_rows = 0
    human_rows = 0
    mapped_rows = 0
    dropped_species = 0
    dropped_no_rna = 0
    dropped_no_disease = 0

    print(f"Processing RNADisease v{version} from: {input_path}")
    for row in iter_rnadisease_rows(input_path):
        if len(row) < 10:
            continue
        total_rows += 1

        rdid = row[0]
        species = row[1]
        rna_symbol = row[2]
        rna_type = row[3]
        disease_name = row[4]
        doid = row[5]
        mesh_id = row[6]
        kegg_id = row[7]
        pmid = row[8]
        score = row[9]

        if species != "Homo sapiens":
            dropped_species += 1
            continue
        human_rows += 1

        # 1. Resolve RNA strictly to RNACENTRAL (zero synthetic fallbacks)
        rna_id = match_rna_to_rnacentral(
            rna_symbol, rna_type, mir_index, ensg_index, noncode_index, symbol_to_ensg
        )
        if not rna_id:
            dropped_no_rna += 1
            continue

        # 2. Resolve Disease strictly to MONDO (zero synthetic fallbacks)
        mondo_id = match_disease_to_mondo(
            doid, mesh_id, disease_name, doid_index, mesh_index, name_index
        )
        if not mondo_id:
            dropped_no_disease += 1
            continue

        mapped_rows += 1

        # 3. Add Nodes
        if rna_id not in nodes:
            nodes[rna_id] = {
                "id": rna_id,
                "category": "biolink:RNAProduct",
                "name": rna_symbol,
                "provided_by": f"RNADisease v{version}",
            }

        if mondo_id not in nodes:
            nodes[mondo_id] = {
                "id": mondo_id,
                "category": "biolink:Disease",
                "name": disease_name,
                "provided_by": f"RNADisease v{version}",
            }

        # 4. Add Edge
        pub_field = f"PMID:{pmid}" if pmid.isdigit() else ""
        edge_key = (rna_id, mondo_id, pub_field, rdid)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)

        edges.append({
            "subject": rna_id,
            "predicate": "biolink:associated_with",
            "object": mondo_id,
            "category": "biolink:DiseaseToEntityAssociationMixin",
            "score": score,
            "publications": pub_field,
            "rnadisease_id": rdid,
            "knowledge_source": f"RNADisease v{version}",
            "provided_by": f"RNADisease v{version}",
        })

    print("\n--- RNADisease Ingestion Summary ---")
    print(f"Total input rows: {total_rows:,}")
    print(f"Non-human rows filtered: {dropped_species:,}")
    print(f"Human rows: {human_rows:,}")
    print(f"Unmapped RNA rows dropped: {dropped_no_rna:,}")
    print(f"Unmapped Disease rows dropped: {dropped_no_disease:,}")
    print(f"Successfully mapped rows: {mapped_rows:,} ({mapped_rows/human_rows*100:.1f}%)")
    print(f"Unique KGX nodes: {len(nodes):,}")
    print(f"Unique KGX edges: {len(edges):,}")

    os.makedirs(os.path.dirname(nodes_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(edges_path) or ".", exist_ok=True)

    # Write nodes TSV
    print(f"Writing nodes to: {nodes_path}")
    node_fields = ["id", "category", "name", "provided_by"]
    with open(nodes_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=node_fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for n in nodes.values():
            writer.writerow(n)

    # Write edges TSV
    print(f"Writing edges to: {edges_path}")
    edge_fields = [
        "subject",
        "predicate",
        "object",
        "category",
        "score",
        "publications",
        "rnadisease_id",
        "knowledge_source",
        "provided_by",
    ]
    with open(edges_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=edge_fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for e in edges:
            writer.writerow(e)

    print("RNADisease ingestion complete.")


def main():
    args = parse_args()
    process_rnadisease(
        input_path=args.input,
        mondo_json=args.mondo_json,
        rnamapping=args.rnamapping,
        ensemblmapping=args.ensemblmapping,
        noncodemapping=args.noncodemapping,
        genes=args.genes,
        version=args.version,
        nodes_path=args.output[0],
        edges_path=args.output[1],
    )


if __name__ == "__main__":
    main()
