#!/usr/bin/env python
"""
lncbook_to_kgx.py: Ingests LncBook 2.0 (CNCB-NGDC) consensus miRNA-lncRNA interactions into Biolink KGX.

Transforms high-confidence consensus interactions (simultaneously supported by miRanda,
TargetScan, and RNAhybrid) into KGX nodes and edges, linking microRNAs to lncRNA transcripts
and expanding the ncRNA-ncRNA interactome (ceRNA sponging).
"""

import argparse
import csv
import gzip
import os
import re
import sys
from typing import Dict, Optional


def parse_args():
    parser = argparse.ArgumentParser(
        prog="lncbook_to_kgx.py",
        description="Transform LncBook 2.0 consensus interactions into KGX format.",
    )
    parser.add_argument("-i", "--input", required=True, help="Path to LncBook gzipped CSV file.")
    parser.add_argument("-r", "--rnamapping", default=None, help="Path to RNAcentral mapping TSV.")
    parser.add_argument("-v", "--version", default="2.0", help="LncBook database release version.")
    parser.add_argument("-o", "--output", nargs=2, required=True, help="Output paths for nodes.tsv and edges.tsv.")
    return parser.parse_args()


def load_rna_mapping(rnamapping_path: Optional[str]) -> Dict[str, str]:
    """
    Maps miRNA lowercase symbols to canonical RNAcentral URS identifiers.
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


def process_lncbook(input_path: str, rna_index: Dict[str, str], version: str,
                    nodes_path: str, edges_path: str):
    """
    Parses LncBook consensus interactions and writes KGX nodes and edges.
    """
    nodes: Dict[str, Dict[str, str]] = {}
    edges = []

    print(f"Processing LncBook v{version} from: {input_path}")
    open_fn = gzip.open if input_path.endswith(".gz") else open
    with open_fn(input_path, "rt", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        total_rows = 0

        for row in reader:
            if len(row) < 11:
                continue
            total_rows += 1

            gene_id = row[0].strip()
            symbol = row[1].strip()
            transcript_id = row[3].strip()
            start_pos = row[4].strip()
            end_pos = row[5].strip()
            energy = row[6].strip()
            algos = row[7].strip()
            mir_raw = row[10].strip()

            if not mir_raw or not transcript_id:
                continue

            # 1. Resolve miRNA strictly to RNACENTRAL (No fallbacks!)
            mir_clean = mir_raw.lower()
            rna_id = rna_index.get(mir_clean)
            if not rna_id:
                clean_stem = re.sub(r"-[53]p$", "", mir_clean)
                rna_id = rna_index.get(clean_stem)

            if not rna_id:
                continue

            # 2. Resolve lncRNA node
            lnc_id = f"LNCBOOK:{transcript_id}"
            display_name = f"{symbol} ({transcript_id})" if symbol and symbol != "-" else transcript_id

            # Add Nodes
            if rna_id not in nodes:
                nodes[rna_id] = {
                    "id": rna_id,
                    "category": "biolink:RNAProduct",
                    "name": mir_raw,
                    "provided_by": f"LncBook v{version}",
                }

            if lnc_id not in nodes:
                nodes[lnc_id] = {
                    "id": lnc_id,
                    "category": "biolink:RNAProduct",
                    "name": display_name,
                    "provided_by": f"LncBook v{version}",
                }

            # Add Edge
            edges.append({
                "subject": rna_id,
                "predicate": "biolink:interacts_with",
                "object": lnc_id,
                "category": "biolink:PairwiseMolecularInteraction",
                "free_energy": energy,
                "algorithm": algos,
                "start_coord": start_pos,
                "end_coord": end_pos,
                "provided_by": f"LncBook v{version}",
            })

    print(f"LncBook Summary: Processed {total_rows:,} consensus records.")
    print(f"Unique nodes: {len(nodes):,} | Total edges: {len(edges):,}")

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
        fieldnames = ["subject", "predicate", "object", "category", "free_energy", "algorithm", "start_coord", "end_coord", "provided_by"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for e in edges:
            writer.writerow(e)
    print(f"Saved edges to: {edges_path}")


def main():
    args = parse_args()
    rna_index = load_rna_mapping(args.rnamapping)
    process_lncbook(
        input_path=args.input,
        rna_index=rna_index,
        version=args.version,
        nodes_path=args.output[0],
        edges_path=args.output[1],
    )


if __name__ == "__main__":
    main()
