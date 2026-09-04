#!/usr/bin/env python
"""
hmdd_to_kgx.py: Ingests HMDD v4.0 (Human microRNA Disease Database) into Biolink-compliant KGX format.

Parses experimentally supported human miRNA-disease associations, maps diseases strictly to MONDO CURIEs
via MeSH normalization, labels, and synonyms, maps miRNAs strictly to canonical RNACENTRAL:URS... CURIEs
(no fallbacks), and produces strongly-typed KGX TSVs linking RNAProduct directly to Disease.
"""

import argparse
import csv
import json
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple


def parse_args():
    parser = argparse.ArgumentParser(
        prog="hmdd_to_kgx.py",
        description="Transform HMDD v4.0 into KGX format with strict Biolink CURIEs.",
    )
    parser.add_argument("-i", "--input", required=True, help="Path to HMDD raw file (alldata_v4.txt).")
    parser.add_argument("-m", "--mondo-json", default="../data/raw/mondo.json", help="Path to mondo.json.")
    parser.add_argument("-r", "--rnamapping", default=None, help="Path to RNAcentral mapping TSV.")
    parser.add_argument("-v", "--version", default="4.0", help="HMDD database release version.")
    parser.add_argument("-o", "--output", nargs=2, required=True, help="Output paths for nodes.tsv and edges.tsv.")
    return parser.parse_args()


def load_mondo_synonym_index(mondo_json_path: str) -> Dict[str, str]:
    """
    Builds a normalized lowercase lookup table from disease names and synonyms to MONDO CURIEs,
    indexing both exact names and punctuation-normalized variants.
    """
    name_to_mondo = {}
    if not os.path.exists(mondo_json_path):
        print(f"Warning: {mondo_json_path} not found. Skipping MONDO label index.")
        return name_to_mondo

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
                        if val.startswith("MESH:"):
                            name_to_mondo[val] = curie

    return name_to_mondo


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


def match_disease_to_mondo(raw_name: str, mondo_index: Dict[str, str]) -> Optional[str]:
    """
    Attempts hierarchical matching of MeSH / clinical disease names to MONDO.
    """
    s = raw_name.strip().lower()
    if s in MESH_DIRECT_MAP:
        return MESH_DIRECT_MAP[s]

    if s in mondo_index:
        return mondo_index[s]

    s_clean = s.replace("-", " ")
    if s_clean in mondo_index:
        return mondo_index[s_clean]

    # Try plural normalization (Neoplasms -> neoplasm / cancer, Diseases -> disease, Injuries -> injury)
    plural_patterns = [
        (r"\bneoplasms\b", "neoplasm"),
        (r"\bneoplasms\b", "cancer"),
        (r"\bdiseases\b", "disease"),
        (r"\binjuries\b", "injury"),
    ]
    for pat, rep in plural_patterns:
        cand = re.sub(pat, rep, s_clean)
        if cand in mondo_index:
            return mondo_index[cand]

    # Inverted MeSH matching: "Carcinoma, Hepatocellular" -> "hepatocellular carcinoma"
    if "," in s:
        parts = [p.strip() for p in s.split(",")]
        rev = " ".join(reversed(parts))
        rev_clean = rev.replace("-", " ")
        if rev in mondo_index:
            return mondo_index[rev]
        if rev_clean in mondo_index:
            return mondo_index[rev_clean]
        for pat, rep in plural_patterns:
            cand = re.sub(pat, rep, rev_clean)
            if cand in mondo_index:
                return mondo_index[cand]

    return None


def load_rna_mapping(rnamapping_path: Optional[str]) -> Dict[str, str]:
    """
    Maps miRNA lowercase symbols and mature forms to canonical RNAcentral URS identifiers.
    """
    mir_to_urs = {}
    if not rnamapping_path or not os.path.exists(rnamapping_path):
        return mir_to_urs

    with open(rnamapping_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 3:
                urs = parts[0].strip()
                mir_name = parts[2].strip().lower()
                mir_to_urs[mir_name] = f"RNACENTRAL:{urs}"
                # Also index base stem without strand
                clean_stem = re.sub(r"-[53]p$", "", mir_name)
                if clean_stem not in mir_to_urs:
                    mir_to_urs[clean_stem] = f"RNACENTRAL:{urs}"

    return mir_to_urs


def process_hmdd(input_path: str, mondo_index: Dict[str, str], rna_index: Dict[str, str],
                 version: str, nodes_path: str, edges_path: str):
    """
    Parses HMDD records and outputs strictly compliant Biolink nodes and edges.
    Enforces strict RNACENTRAL:URS... and MONDO:... namespaces with zero fallbacks.
    """
    nodes: Dict[str, Dict[str, str]] = {}
    edges = []
    seen_edges = set()

    print(f"Processing HMDD v{version} from: {input_path}")
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)

        total_rows = 0
        mapped_rows = 0
        dropped_no_mondo = 0
        dropped_no_rna = 0

        for row in reader:
            if len(row) < 4:
                continue
            total_rows += 1

            code = row[0].strip() if len(row) > 0 else ""
            pmid = row[1].strip() if len(row) > 1 else ""
            mir_raw = row[2].strip() if len(row) > 2 else ""
            dis_raw = row[3].strip() if len(row) > 3 else ""
            desc = row[4].strip() if len(row) > 4 else ""

            # 1. Resolve Disease strictly to MONDO
            mondo_id = match_disease_to_mondo(dis_raw, mondo_index)
            if not mondo_id:
                dropped_no_mondo += 1
                continue

            # 2. Resolve MicroRNA strictly to RNACENTRAL (No fallbacks!)
            mir_clean = mir_raw.lower()
            rna_id = rna_index.get(mir_clean)
            if not rna_id:
                clean_stem = re.sub(r"-[53]p$", "", mir_clean)
                rna_id = rna_index.get(clean_stem)

            if not rna_id:
                dropped_no_rna += 1
                continue

            # 3. Add Nodes
            if rna_id not in nodes:
                nodes[rna_id] = {
                    "id": rna_id,
                    "category": "biolink:RNAProduct",
                    "name": mir_raw,
                    "provided_by": f"HMDD v{version}",
                }

            if mondo_id not in nodes:
                nodes[mondo_id] = {
                    "id": mondo_id,
                    "category": "biolink:Disease",
                    "name": dis_raw,
                    "provided_by": f"HMDD v{version}",
                }

            # 4. Add Edge
            pub_field = f"PMID:{pmid}" if pmid.isdigit() else ""
            edge_key = (rna_id, mondo_id, pub_field, code)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            edges.append({
                "subject": rna_id,
                "predicate": "biolink:associated_with",
                "object": mondo_id,
                "category": "biolink:DiseaseToEntityAssociationMixin",
                "evidence_code": code,
                "publications": pub_field,
                "description": desc,
                "provided_by": f"HMDD v{version}",
            })
            mapped_rows += 1

    print(f"HMDD Summary: Processed {total_rows:,} raw records.")
    print(f"  Mapped edges: {mapped_rows:,}")
    print(f"  Dropped (unmapped disease): {dropped_no_mondo:,}")
    print(f"  Dropped (unmapped to RNAcentral): {dropped_no_rna:,}")
    print(f"Unique nodes: {len(nodes):,} | Unique edges: {len(edges):,}")

    # Write nodes TSV with strict \n line endings
    os.makedirs(os.path.dirname(nodes_path), exist_ok=True)
    with open(nodes_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "category", "name", "provided_by"], delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for n in nodes.values():
            writer.writerow(n)
    print(f"Saved nodes to: {nodes_path}")

    # Write edges TSV with strict \n line endings
    os.makedirs(os.path.dirname(edges_path), exist_ok=True)
    with open(edges_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["subject", "predicate", "object", "category", "evidence_code", "publications", "description", "provided_by"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for e in edges:
            writer.writerow(e)
    print(f"Saved edges to: {edges_path}")


def main():
    args = parse_args()
    mondo_index = load_mondo_synonym_index(args.mondo_json)
    rna_index = load_rna_mapping(args.rnamapping)
    process_hmdd(
        input_path=args.input,
        mondo_index=mondo_index,
        rna_index=rna_index,
        version=args.version,
        nodes_path=args.output[0],
        edges_path=args.output[1],
    )


if __name__ == "__main__":
    main()
