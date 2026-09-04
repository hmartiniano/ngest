#!/usr/bin/env python
"""
tarbase_to_kgx.py: Ingests DIANA-TarBase v9.0 into Biolink KGX format.

Enforces strict Biolink CURIE namespaces:
  - RNAs: strictly canonical RNACENTRAL:URS... (resolves mature -3p/-5p arm suffixes)
  - Genes: strictly canonical NCBIGene:<entrez_id> via Ensembl-to-Entrez index
Preserves experimental assay methods, validation types (Direct vs High-throughput),
and PubMed citations with pure Unix LF line endings.
"""

import argparse
import csv
import gzip
import os
import re
import sys
import uuid
from typing import Dict, Optional

import pandas as pd


DIRECT_METHODS = {
    "Luciferase Reporter Assay",
    "Western Blot",
    "qPCR",
    "Northern Blot",
    "Biotin-qPCR",
    "ELISA",
    "Immunohistochemistry",
    "Immunofluorescence",
    "2D-DIGE",
}


def get_parser():
    parser = argparse.ArgumentParser(
        prog="tarbase_to_kgx.py",
        description="Convert DIANA-TarBase TSV to KGX nodes and edges format with strict Biolink CURIEs.",
    )
    parser.add_argument("-i", "--input", required=True, help="Input TarBase tsv.gz file")
    parser.add_argument("-r", "--rna", required=True, help="Input RNACentral TarBase mapping file")
    parser.add_argument("-e", "--entrez-mapping", default="../data/processed/mappings/ensembl_to_entrez.tsv",
                        help="Path to Ensembl-to-Entrez mapping TSV.")
    parser.add_argument("-v", "--version", default="9.0", help="TarBase version")
    parser.add_argument(
        "--direct-only",
        action="store_true",
        default=False,
        help="Filter to retain only direct wet-lab validation assays",
    )
    parser.add_argument(
        "--assay-type",
        default=None,
        help="Comma-separated list of specific assay methods to retain",
    )
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default=["tarbase_nodes.tsv", "tarbase_edges.tsv"],
        help="Output files: [nodes.tsv, edges.tsv]",
    )
    return parser


def load_rna_mapping(rna_path: str) -> Dict[str, str]:
    mir_to_urs = {}
    with open(rna_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 3:
                urs = parts[0].strip()
                name = parts[2].strip().lower()
                mir_to_urs[name] = urs
                stem = re.sub(r"-[53]p$", "", name)
                if stem not in mir_to_urs:
                    mir_to_urs[stem] = urs
    return mir_to_urs


def load_entrez_mapping(entrez_path: str) -> Dict[str, str]:
    ens_to_entrez = {}
    if not os.path.exists(entrez_path):
        print(f"Warning: {entrez_path} not found.")
        return ens_to_entrez
    with open(entrez_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
        for row in reader:
            if len(row) >= 2:
                entrez = row[0].strip()
                ensembl = row[1].strip()
                if entrez and ensembl:
                    ens_to_entrez[ensembl] = entrez
    return ens_to_entrez


def main():
    parser = get_parser()
    args = parser.parse_args()

    print(f"Loading RNAcentral mapping from: {args.rna}")
    mir_to_urs = load_rna_mapping(args.rna)

    print(f"Loading Ensembl to Entrez mapping from: {args.entrez_mapping}")
    ens_to_entrez = load_entrez_mapping(args.entrez_mapping)

    print(f"Loading TarBase from: {args.input}")
    tarbase = pd.read_csv(args.input, sep="\t", low_memory=False)

    # Filter to human
    if "species" in tarbase.columns:
        tarbase = tarbase[tarbase["species"] == "Homo sapiens"]

    # Optional assay filtering
    if args.direct_only and "experimental_method" in tarbase.columns:
        tarbase = tarbase[tarbase["experimental_method"].isin(DIRECT_METHODS)]
    elif args.assay_type and "experimental_method" in tarbase.columns:
        allowed = [x.strip() for x in args.assay_type.split(",")]
        tarbase = tarbase[tarbase["experimental_method"].isin(allowed)]

    # 1. Map MicroRNAs strictly to RNACENTRAL (resolves arm suffixes -3p/-5p)
    def map_mir(m):
        s = str(m).strip().lower()
        if s in mir_to_urs:
            return mir_to_urs[s]
        stem = re.sub(r"-[53]p$", "", s)
        return mir_to_urs.get(stem, None)

    tarbase["subject_urs"] = tarbase["mirna_name"].apply(map_mir)

    # 2. Map Genes strictly to NCBIGene
    tarbase["object_entrez"] = tarbase["gene_id"].astype(str).map(ens_to_entrez)

    # Filter for strict compliance (no fallbacks)
    tarbase = tarbase.dropna(subset=["subject_urs", "object_entrez"])

    tarbase["subject"] = "RNACENTRAL:" + tarbase["subject_urs"]
    tarbase["object"] = "NCBIGene:" + tarbase["object_entrez"]
    tarbase["provided_by"] = "DIANA-TarBase"
    tarbase["knowledge_source"] = "DIANA-TarBase"
    tarbase["predicate"] = "biolink:interacts_with"
    tarbase["relation"] = "RO:0002434"
    tarbase["source"] = "DIANA-TarBase"
    tarbase["source version"] = str(args.version)

    # Add evidence annotations
    if "experimental_method" in tarbase.columns:
        tarbase["assay_type"] = tarbase["experimental_method"].fillna("")
        tarbase["validation_type"] = tarbase["experimental_method"].apply(
            lambda m: "Direct" if m in DIRECT_METHODS else "High-throughput"
        )
    else:
        tarbase["assay_type"] = ""
        tarbase["validation_type"] = ""

    if "article_pubmed_id" in tarbase.columns:
        tarbase["publications"] = tarbase["article_pubmed_id"].apply(
            lambda p: f"PMID:{int(p)}" if pd.notnull(p) and str(p).replace('.', '').isdigit() else ""
        )
    else:
        tarbase["publications"] = ""

    if "confidence" in tarbase.columns:
        tarbase["has_confidence_level"] = pd.to_numeric(tarbase["confidence"], errors="coerce").fillna(1.0)
    else:
        tarbase["has_confidence_level"] = 1.0

    edge_cols = [
        "subject",
        "predicate",
        "object",
        "knowledge_source",
        "relation",
        "assay_type",
        "validation_type",
        "publications",
        "has_confidence_level",
        "source",
        "source version",
    ]
    edges = tarbase[edge_cols].drop_duplicates()
    edges["id"] = edges["subject"].apply(lambda x: uuid.uuid4())

    # Build unique nodes
    rna = tarbase[["subject", "mirna_name", "provided_by", "source", "source version"]].copy()
    rna["id"] = rna["subject"]
    rna["name"] = rna["mirna_name"]
    rna["category"] = "biolink:RNAProduct"
    rna = rna[["id", "name", "category", "provided_by", "source", "source version"]].drop_duplicates()

    genes = tarbase[["object", "gene_name", "provided_by", "source", "source version"]].copy()
    genes["id"] = genes["object"]
    genes["name"] = genes["gene_name"]
    genes["category"] = "biolink:Gene"
    genes = genes[["id", "name", "category", "provided_by", "source", "source version"]].drop_duplicates()

    nodes = pd.concat([genes, rna], ignore_index=True).drop_duplicates(subset=["id"])

    # Write TSVs with strict Unix \n
    os.makedirs(os.path.dirname(args.output[0]), exist_ok=True)
    os.makedirs(os.path.dirname(args.output[1]), exist_ok=True)
    nodes.to_csv(args.output[0], sep="\t", index=False, lineterminator="\n")
    edges.to_csv(args.output[1], sep="\t", index=False, lineterminator="\n")
    print(f"Saved {len(nodes):,} nodes to {args.output[0]} and {len(edges):,} edges to {args.output[1]}")


if __name__ == "__main__":
    main()
