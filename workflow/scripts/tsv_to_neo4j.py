#!/usr/bin/env python
"""
This script processes TSV files or a .tar.gz archive from KGX for import into Neo4j
using the neo4j-admin import tool.
"""
import argparse
import os
import re
import sys
import tarfile
import numpy as np
import pandas as pd


def process_nodes(source, output_path):
    df = pd.read_csv(source, sep="\t", low_memory=False)
    rename_cols = {}
    if "category" in df.columns:
        rename_cols["category"] = "category:LABEL"
    if "id" in df.columns:
        rename_cols["id"] = "id:ID"
    df = df.rename(columns=rename_cols)

    if "name" in df.columns and "id:ID" in df.columns:
        df["name"] = np.where(df["name"].isnull(), df["id:ID"], df["name"])
    elif "id:ID" in df.columns:
        df["name"] = df["id:ID"]

    if "xref" in df.columns:
        df["xref"] = df["xref"].fillna("").astype(str).str.replace("|", ";", regex=False)

    if "category:LABEL" in df.columns:
        df["category:LABEL"] = df["category:LABEL"].astype(str) + ";biolink:NamedThing"

    df.to_csv(output_path, index=False, compression="gzip")
    print(f"Saved processed nodes to {output_path} ({len(df)} nodes)")


TYPE_MAPPINGS_EDGES = {
    "predicate": "predicate:TYPE",
    "subject": "subject:START_ID",
    "object": "object:END_ID",
    "confidence_score": "confidence_score:float",
    "has_confidence_level": "has_confidence_level:float",
    "combined_score": "combined_score:int",
    "fdr": "fdr:float",
    "expression_score": "expression_score:float",
    "expression_rank": "expression_rank:float",
    "publications": "publications:string[]",
    "assay_type": "assay_type:string",
    "validation_type": "validation_type:string",
    "call_quality": "call_quality:string",
    "interaction_level": "interaction_level:string",
    "relation": "relation:string",
    "knowledge_source": "knowledge_source:string",
    "source": "source:string",
    "source version": "source_version:string",
}


def process_edges(source, output_path, chunksize=1_000_000):
    total_edges = 0
    first_chunk = True

    for chunk in pd.read_csv(source, sep="\t", chunksize=chunksize, low_memory=False):
        rename_cols = {col: TYPE_MAPPINGS_EDGES[col] for col in chunk.columns if col in TYPE_MAPPINGS_EDGES}
        chunk = chunk.rename(columns=rename_cols)

        # Format array fields if present
        if "publications:string[]" in chunk.columns:
            chunk["publications:string[]"] = (
                chunk["publications:string[]"]
                .fillna("")
                .astype(str)
                .str.replace("|", ";", regex=False)
            )

        # Convert any empty strings in float columns to NaN so Neo4j imports cleanly
        for col in chunk.columns:
            if col.endswith(":float"):
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
            elif col.endswith(":int"):
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce").astype("Int64")

        mode = "w" if first_chunk else "a"
        header = first_chunk
        chunk.to_csv(output_path, index=False, header=header, mode=mode, compression="gzip")
        total_edges += len(chunk)
        first_chunk = False

    print(f"Saved processed edges to {output_path} ({total_edges} edges)")


def get_parser():
    parser = argparse.ArgumentParser(
        prog="tsv_to_neo4j.py",
        description="Convert KGX TSV files or .tar.gz archive to Neo4j admin import CSV format with typed properties.",
    )
    parser.add_argument(
        "-i", "--input", help="Input .tar.gz archive containing nodes and edges TSVs"
    )
    parser.add_argument("-n", "--nodes", help="Input nodes TSV file")
    parser.add_argument("-e", "--edges", help="Input edges TSV file")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Output directory for nodes.csv.gz and edges.csv.gz. Default: current directory",
    )
    parser.add_argument(
        "positional_args",
        nargs="*",
        help="Optional positional arguments: [nodes.tsv edges.tsv] for backwards compatibility",
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    nodes_out = os.path.join(args.output_dir, "nodes.csv.gz")
    edges_out = os.path.join(args.output_dir, "edges.csv.gz")

    if args.input:
        with tarfile.open(args.input, "r:*") as tar:
            nodes_member = None
            edges_member = None
            while True:
                member = tar.next()
                if member is None:
                    break
                if not nodes_member and re.search(r"nodes\.tsv$", member.name):
                    nodes_member = member
                elif not edges_member and re.search(r"edges\.tsv$", member.name):
                    edges_member = member
                if nodes_member and edges_member:
                    break

            if not nodes_member or not edges_member:
                raise ValueError(
                    f"Archive {args.input} must contain both a nodes.tsv and edges.tsv file."
                )

            print(f"Processing nodes from archive: {nodes_member.name}")
            with tar.extractfile(nodes_member) as f:
                process_nodes(f, nodes_out)

            print(f"Processing edges from archive: {edges_member.name}")
            with tar.extractfile(edges_member) as f:
                process_edges(f, edges_out)
    else:
        nodes_file = args.nodes
        edges_file = args.edges
        if not nodes_file and len(args.positional_args) >= 1:
            nodes_file = args.positional_args[0]
        if not edges_file and len(args.positional_args) >= 2:
            edges_file = args.positional_args[1]

        if not nodes_file or not edges_file:
            parser.error(
                "Either specify -i/--input (archive) or both --nodes and --edges (or positional arguments)."
            )

        process_nodes(nodes_file, nodes_out)
        process_edges(edges_file, edges_out)


if __name__ == "__main__":
    main()
