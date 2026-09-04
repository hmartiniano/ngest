#!/usr/bin/env python
"""
mirtarbase_to_kgx.py: Ingests miRTarBase 10.0 (2025) human miRNA-target interactions into Biolink KGX.

Enforces strict Biolink Model CURIE namespaces:
  - RNAs: strictly canonical RNACENTRAL:URS... (no MIRBASE fallback)
  - Genes: strictly canonical NCBIGene:<entrez_id> (no ENSEMBL/HGNC fallbacks)
Preserves experimental validation methods (Luciferase, Western blot, qPCR), evidence types,
and PubMed citations with pure Unix LF line endings.
"""

import argparse
import csv
import gzip
import os
import re
import sys
from typing import Dict, List, Optional, Set


def parse_args():
    parser = argparse.ArgumentParser(
        prog="mirtarbase_to_kgx.py",
        description="Transform miRTarBase 10.0 hsa_MTI into KGX with strict Biolink CURIEs.",
    )
    parser.add_argument("-i", "--input", required=True, help="Path to hsa_MTI.csv (or .csv.gz).")
    parser.add_argument("-r", "--rnamapping", default="../data/processed/mappings/rnacentral_tarbase_human_mapping.tsv",
                        help="Path to RNAcentral mapping TSV.")
    parser.add_argument("-v", "--version", default="10.0", help="miRTarBase database release version.")
    parser.add_argument("--strong-only", action="store_true", help="Filter for Strong Evidence interactions only.")
    parser.add_argument("-o", "--output", nargs=2, required=True, help="Output paths for nodes.tsv and edges.tsv.")
    return parser.parse_args()


def load_rna_mapping(rnamapping_path: Optional[str]) -> Dict[str, str]:
    """
    Maps miRNA lowercase symbols and arm-specific mature forms to canonical RNAcentral URS identifiers.
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
                clean_stem = re.sub(r"-[53]p$", "", mir_name)
                if clean_stem not in mir_to_urs:
                    mir_to_urs[clean_stem] = f"RNACENTRAL:{urs}"

    return mir_to_urs


def process_mirtarbase(input_path: str, rna_index: Dict[str, str], version: str,
                       strong_only: bool, nodes_path: str, edges_path: str):
    """
    Parses miRTarBase hsa_MTI.csv and outputs strictly compliant Biolink nodes and edges.
    Enforces strict RNACENTRAL:URS... and NCBIGene:... namespaces with zero fallbacks.
    """
    nodes: Dict[str, Dict[str, str]] = {}
    edges = []
    seen_edges = set()

    print(f"Processing miRTarBase v{version} from: {input_path}")
    open_fn = gzip.open if input_path.endswith(".gz") else open
    with open_fn(input_path, "rt", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        total_rows = 0
        mapped_rows = 0
        dropped_no_rna = 0
        dropped_no_gene = 0

        for row in reader:
            total_rows += 1
            mir_raw = row.get("miRNA", "").strip()
            target_symbol = row.get("Target Gene", "").strip()
            entrez_id_raw = row.get("Target Gene (Entrez ID)", "").strip()
            experiments = row.get("Experiments", "").strip()
            support_type = row.get("Support Type", "").strip()
            pmid_raw = row.get("References (PMID)", "").strip()
            mirt_id = row.get("miRTarBase ID", "").strip()

            if strong_only and "strong" not in support_type.lower():
                continue

            # Clean Entrez ID
            entrez_id = entrez_id_raw[:-2] if entrez_id_raw.endswith(".0") else entrez_id_raw
            pmid = pmid_raw[:-2] if pmid_raw.endswith(".0") else pmid_raw

            # 1. Resolve Target Gene strictly to NCBIGene (No fallbacks!)
            if not entrez_id or not entrez_id.isdigit():
                dropped_no_gene += 1
                continue
            gene_id = f"NCBIGene:{entrez_id}"

            # 2. Resolve miRNA strictly to RNACENTRAL (No fallbacks!)
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
                    "provided_by": f"miRTarBase v{version}",
                }

            if gene_id not in nodes:
                nodes[gene_id] = {
                    "id": gene_id,
                    "category": "biolink:Gene",
                    "name": target_symbol if target_symbol else entrez_id,
                    "provided_by": f"miRTarBase v{version}",
                }

            # 4. Add Edge
            pub_field = f"PMID:{pmid}" if pmid and pmid.isdigit() else ""
            edge_key = (rna_id, gene_id, pub_field, support_type)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            edges.append({
                "subject": rna_id,
                "predicate": "biolink:interacts_with",
                "object": gene_id,
                "category": "biolink:PairwiseMolecularInteraction",
                "publications": pub_field,
                "validation_type": support_type,
                "assay_type": experiments,
                "mirtarbase_id": mirt_id,
                "provided_by": f"miRTarBase v{version}",
            })
            mapped_rows += 1

    print(f"miRTarBase Summary: Read {total_rows:,} records.")
    print(f"  Mapped edges: {mapped_rows:,}")
    print(f"  Dropped (unmapped to RNAcentral): {dropped_no_rna:,}")
    print(f"  Dropped (invalid/missing Entrez ID): {dropped_no_gene:,}")
    print(f"Unique nodes: {len(nodes):,} | Unique edges: {len(edges):,}")

    # Write nodes TSV with strict Unix \n
    os.makedirs(os.path.dirname(nodes_path), exist_ok=True)
    with open(nodes_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "category", "name", "provided_by"], delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for n in nodes.values():
            writer.writerow(n)
    print(f"Saved nodes to: {nodes_path}")

    # Write edges TSV with strict Unix \n
    os.makedirs(os.path.dirname(edges_path), exist_ok=True)
    with open(edges_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["subject", "predicate", "object", "category", "publications", "validation_type", "assay_type", "mirtarbase_id", "provided_by"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for e in edges:
            writer.writerow(e)
    print(f"Saved edges to: {edges_path}")


def main():
    args = parse_args()
    rna_index = load_rna_mapping(args.rnamapping)
    process_mirtarbase(
        input_path=args.input,
        rna_index=rna_index,
        version=args.version,
        strong_only=args.strong_only,
        nodes_path=args.output[0],
        edges_path=args.output[1],
    )

# execute the code if it is run as main script
if __name__ == "__main__":
    main()
