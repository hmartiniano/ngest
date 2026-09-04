#!/usr/bin/env python
"""
graph_analysis.py: Core analysis, I/O, and reporting engine for ngest Knowledge Graphs.

Supports direct streaming from .tar.gz archives (e.g. lcc.tar.gz, merged.tar.gz),
multi-source provenance unravelling, memory-optimized metagraph schema generation,
dynamic database discovery from YAML config, and figure/table export.
"""

import argparse
import os
import re
import sys
import tarfile
from collections import Counter
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yaml


# =============================================================================
# 1. Archive & Table I/O Utilities
# =============================================================================

def resolve_archive_members(tar: tarfile.TarFile) -> Tuple[Optional[tarfile.TarInfo], Optional[tarfile.TarInfo]]:
    """
    Fast sequential lookup of nodes.tsv and edges.tsv members in a tar archive.
    Uses tar.next() to avoid traversing the entire archive.
    """
    nodes_member = None
    edges_member = None
    while True:
        member = tar.next()
        if member is None:
            break
        if re.search(r"nodes\.tsv$", member.name):
            nodes_member = member
        elif re.search(r"edges\.tsv$", member.name):
            edges_member = member
        if nodes_member and edges_member:
            break
    return nodes_member, edges_member


def clean_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).replace("\r", "").strip() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def load_nodes(
    source: str,
    usecols: Optional[List[str]] = None,
    nrows: Optional[int] = None,
    low_memory: bool = False,
) -> pd.DataFrame:
    """
    Load nodes table from a .tar.gz archive, a .tsv.gz, or a plain .tsv file.
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source file not found: {source}")

    if source.endswith(".tar.gz") or source.endswith(".tar"):
        with tarfile.open(source, "r:*") as tar:
            nodes_member, _ = resolve_archive_members(tar)
            if not nodes_member:
                raise ValueError(f"Archive {source} does not contain a *nodes.tsv file.")
            with tar.extractfile(nodes_member) as f:
                df = pd.read_csv(f, sep="\t", nrows=nrows, low_memory=low_memory)
                df = clean_df_columns(df)
                if usecols:
                    avail = [c for c in usecols if c in df.columns]
                    df = df[avail]
                return df
    else:
        df = pd.read_csv(source, sep="\t", nrows=nrows, low_memory=low_memory)
        df = clean_df_columns(df)
        if usecols:
            avail = [c for c in usecols if c in df.columns]
            df = df[avail]
        return df


def load_edges(
    source: str,
    usecols: Optional[List[str]] = None,
    nrows: Optional[int] = None,
    chunksize: Optional[int] = None,
    dtype: Optional[Dict[str, Any]] = None,
    low_memory: bool = False,
) -> Union[pd.DataFrame, Generator[pd.DataFrame, None, None]]:
    """
    Load edges table from a .tar.gz archive, a .tsv.gz, or a plain .tsv file.
    Supports chunked loading for large edge sets.
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source file not found: {source}")

    if source.endswith(".tar.gz") or source.endswith(".tar"):
        tar = tarfile.open(source, "r:*")
        _, edges_member = resolve_archive_members(tar)
        if not edges_member:
            tar.close()
            raise ValueError(f"Archive {source} does not contain a *edges.tsv file.")
        f = tar.extractfile(edges_member)
        if chunksize:
            def chunk_generator():
                try:
                    for chunk in pd.read_csv(f, sep="\t", nrows=nrows, chunksize=chunksize, dtype=dtype, low_memory=low_memory):
                        chunk = clean_df_columns(chunk)
                        if usecols:
                            avail = [c for c in usecols if c in chunk.columns]
                            chunk = chunk[avail]
                        yield chunk
                finally:
                    f.close()
                    tar.close()
            return chunk_generator()
        else:
            with f:
                df = pd.read_csv(f, sep="\t", nrows=nrows, dtype=dtype, low_memory=low_memory)
                df = clean_df_columns(df)
                if usecols:
                    avail = [c for c in usecols if c in df.columns]
                    df = df[avail]
            tar.close()
            return df
    else:
        if chunksize:
            def plain_generator():
                for chunk in pd.read_csv(source, sep="\t", nrows=nrows, chunksize=chunksize, dtype=dtype, low_memory=low_memory):
                    chunk = clean_df_columns(chunk)
                    if usecols:
                        avail = [c for c in usecols if c in chunk.columns]
                        chunk = chunk[avail]
                    yield chunk
            return plain_generator()
        df = pd.read_csv(source, sep="\t", nrows=nrows, dtype=dtype, low_memory=low_memory)
        df = clean_df_columns(df)
        if usecols:
            avail = [c for c in usecols if c in df.columns]
            df = df[avail]
        return df


def load_graph_data(
    source: str,
    nodes_usecols: Optional[List[str]] = None,
    edges_usecols: Optional[List[str]] = None,
    nrows_edges: Optional[int] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convenience loader that extracts both nodes and edges dataframes from a .tar.gz archive.
    """
    if source.endswith(".tar.gz") or source.endswith(".tar"):
        with tarfile.open(source, "r:*") as tar:
            nodes_member, edges_member = resolve_archive_members(tar)
            if not nodes_member or not edges_member:
                raise ValueError(f"Archive {source} must contain both *nodes.tsv and *edges.tsv.")
            with tar.extractfile(nodes_member) as fn:
                nodes_df = pd.read_csv(fn, sep="\t", usecols=nodes_usecols, low_memory=False)
            with tar.extractfile(edges_member) as fe:
                edges_df = pd.read_csv(fe, sep="\t", usecols=edges_usecols, nrows=nrows_edges, low_memory=False)
        return nodes_df, edges_df
    else:
        raise ValueError("load_graph_data expects an archive path (.tar.gz). Use load_nodes and load_edges for individual files.")


# =============================================================================
# 2. Dynamic Database Configuration Discovery
# =============================================================================

def load_active_databases(config_path: str = "config/databases_config.yaml") -> pd.DataFrame:
    """
    Parse databases_config.yaml to discover active databases and their node/edge file paths.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    df = pd.DataFrame(config.get("databases", []))
    return df


# =============================================================================
# 3. Pre-Merge Analysis (Individual Processed Databases)
# =============================================================================

def analyze_processed_databases(
    config_path: str = "config/databases_config.yaml",
    base_dir: str = ".",
) -> Dict[str, Any]:
    """
    Analyze node categories, CURIE prefixes, unique entities, and edge predicates
    across all active databases declared in databases_config.yaml.
    """
    databases = load_active_databases(config_path)

    category_dict = {}
    prefix_dict = {}
    predicate_dict = {}
    nodes_collector = []
    edges_collector = []

    config_dir = os.path.dirname(os.path.abspath(config_path))

    for _, row in databases.iterrows():
        db_name = row["name"]
        nodes_path = os.path.normpath(os.path.join(config_dir, row["nodes"]))
        edges_path = os.path.normpath(os.path.join(config_dir, row["edges"]))
        if not os.path.exists(nodes_path) and base_dir:
            nodes_path = os.path.normpath(os.path.join(base_dir, os.path.basename(row["nodes"])))
        if not os.path.exists(edges_path) and base_dir:
            edges_path = os.path.normpath(os.path.join(base_dir, os.path.basename(row["edges"])))

        if os.path.exists(nodes_path):
            ndf = pd.read_csv(nodes_path, sep="\t", usecols=["id", "category", "provided_by"], low_memory=False)
            category_dict[db_name] = ndf["category"].value_counts().to_dict()
            prefix_dict[db_name] = ndf["id"].dropna().str.split(":").str[0].value_counts().to_dict()

            ninfo = ndf[["id", "category", "provided_by"]].copy()
            ninfo["DB"] = db_name
            nodes_collector.append(ninfo)

        if os.path.exists(edges_path):
            edf = pd.read_csv(edges_path, sep="\t", usecols=["subject", "predicate", "object"], low_memory=False)
            predicate_dict[db_name] = edf["predicate"].value_counts().to_dict()
            # Sample edges for Sankey pivot if file is very large
            if len(edf) > 500000:
                edf_sample = edf[["subject", "object"]].sample(500000, random_state=42)
            else:
                edf_sample = edf[["subject", "object"]]
            edges_collector.append(edf_sample)

    # Unique nodes across databases
    if nodes_collector:
        all_nodes = pd.concat(nodes_collector, ignore_index=True)
        unique_nodes = all_nodes.drop_duplicates(subset=["id"])
        unique_counts = unique_nodes.groupby(["DB", "category"]).size().unstack(fill_value=0)
    else:
        unique_counts = pd.DataFrame()

    # Subject-Object Prefix Cross-Tabulation (for Sankey)
    if edges_collector:
        all_edges = pd.concat(edges_collector, ignore_index=True)
        all_edges["sub_prefix"] = all_edges["subject"].str.split(":").str[0]
        all_edges["obj_prefix"] = all_edges["object"].str.split(":").str[0]
        sankey_pivot = all_edges.groupby(["sub_prefix", "obj_prefix"]).size().unstack(fill_value=0)
    else:
        sankey_pivot = pd.DataFrame()

    return {
        "categories": pd.DataFrame(category_dict).fillna(0).astype(int),
        "prefixes": pd.DataFrame(prefix_dict).fillna(0).astype(int),
        "unique_nodes": unique_counts,
        "predicates": pd.DataFrame(predicate_dict).fillna(0).astype(int),
        "sankey_pivot": sankey_pivot,
    }


# =============================================================================
# 4. Merged Graph YAML Statistics Analysis
# =============================================================================

def analyze_merged_stats_yaml(
    yaml_path: str = "data/processed/finals/merged_graph_stats.yaml",
) -> Dict[str, Any]:
    """
    Parse KGX's merged_graph_stats.yaml metadata artifact into structured DataFrames.
    """
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Stats YAML file not found: {yaml_path}")

    with open(yaml_path, "r") as f:
        stats = yaml.safe_load(f)

    edge_stats = stats.get("edge_stats", {})
    node_stats = stats.get("node_stats", {})

    total_edges = edge_stats.get("total_edges", 0)
    total_nodes = node_stats.get("total_nodes", 0)

    # Knowledge sources breakdown
    ks_data = edge_stats.get("knowledge_source", [])
    if isinstance(ks_data, dict):
        ks_df = pd.DataFrame(list(ks_data.items()), columns=["knowledge_source", "count"]).sort_values("count", ascending=False)
    else:
        ks_df = pd.DataFrame(ks_data, columns=["knowledge_source"])

    # Predicates by source
    pred_data = edge_stats.get("count_by_predicates", {})
    pred_rows = []
    for pred, details in pred_data.items():
        if pred == "unknown":
            continue
        row = {"predicate": pred, "total": details.get("count", 0)}
        for src, src_details in details.get("knowledge_source", {}).items():
            row[src] = src_details.get("count", 0)
        pred_rows.append(row)
    pred_df = pd.DataFrame(pred_rows).fillna(0)
    if "predicate" in pred_df.columns:
        pred_df = pred_df.sort_values("total", ascending=False).reset_index(drop=True)

    # Subject-Predicate-Object (SPO) patterns
    spo_data = edge_stats.get("count_by_spo", {})
    spo_rows = []
    for spo, details in spo_data.items():
        if spo == "unknown":
            continue
        row = {"spo": spo, "total": details.get("count", 0)}
        for src, src_details in details.get("knowledge_source", {}).items():
            row[src] = src_details.get("count", 0)
        spo_rows.append(row)
    spo_df = pd.DataFrame(spo_rows).fillna(0)
    if "spo" in spo_df.columns:
        spo_df = spo_df.sort_values("total", ascending=False).reset_index(drop=True)

    # Node categories by source
    cat_data = node_stats.get("count_by_category", {})
    cat_rows = []
    for cat, details in cat_data.items():
        if cat == "unknown":
            continue
        row = {"category": cat, "total": details.get("count", 0)}
        for src, src_details in details.get("provided_by", {}).items():
            row[src] = src_details.get("count", 0)
        cat_rows.append(row)
    cat_df = pd.DataFrame(cat_rows).fillna(0)
    if "category" in cat_df.columns:
        cat_df = cat_df.sort_values("total", ascending=False).reset_index(drop=True)

    # Prefixes by category
    pref_data = node_stats.get("count_by_id_prefixes_by_category", {})
    pref_rows = []
    for cat, prefixes in pref_data.items():
        if cat == "unknown":
            continue
        for pref, cnt in prefixes.items():
            pref_rows.append({"category": cat, "prefix": pref, "count": cnt})
    pref_df = pd.DataFrame(pref_rows)

    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "knowledge_sources": ks_df,
        "predicates_by_source": pred_df,
        "spo_by_source": spo_df,
        "categories_by_source": cat_df,
        "prefixes_by_category": pref_df,
    }


# =============================================================================
# 5. Largest Connected Component (LCC) Deep Analysis
# =============================================================================

def analyze_lcc_graph(
    lcc_source: str = "data/processed/finals/lcc.tar.gz",
    output_dir: Optional[str] = None,
    chunksize: int = 2000000,
) -> Dict[str, Any]:
    """
    Perform deep topological, provenance-unravelling, and metagraph schema
    analysis on the Largest Connected Component.
    """
    print(f"Loading LCC nodes from: {lcc_source}")
    nodes = load_nodes(lcc_source, usecols=["id", "category", "source", "provided_by"])
    if "source" not in nodes.columns:
        if "provided_by" in nodes.columns:
            nodes["source"] = nodes["provided_by"]
        else:
            nodes["source"] = "Unknown"

    # Basic node distributions
    total_nodes = len(nodes)
    category_counts = nodes["category"].value_counts()
    prefix_counts = nodes["id"].str.split(":").str[0].value_counts()

    # Explode multi-source nodes
    nodes_exploded = nodes.copy()
    nodes_exploded["source"] = nodes_exploded["source"].fillna("").astype(str).str.split("|")
    nodes_exploded = nodes_exploded.explode("source")
    nodes_exploded["prefix"] = nodes_exploded["id"].str.split(":").str[0]

    categories_by_source = nodes_exploded.groupby(["category", "source"]).size().unstack(fill_value=0)
    prefixes_by_source = nodes_exploded.groupby(["prefix", "source"]).size().unstack(fill_value=0)

    # Build memory-efficient mapping of node_id -> category for edge schema mapping
    print("Building node_id -> category dictionary...")
    id_to_cat = dict(zip(nodes["id"], nodes["category"]))

    # Edge analysis via chunking to keep memory under control
    print(f"Loading and analyzing LCC edges from: {lcc_source}")
    predicate_counter = Counter()
    predicate_source_counter = Counter()
    schema_source_counter = Counter()
    total_edges = 0

    edge_chunks = load_edges(
        lcc_source,
        usecols=["subject", "object", "predicate", "source", "provided_by", "knowledge_source"],
        chunksize=chunksize,
        dtype={"predicate": "category"},
    )

    for chunk in edge_chunks:
        total_edges += len(chunk)
        if "source" not in chunk.columns:
            for alt in ["provided_by", "knowledge_source"]:
                if alt in chunk.columns:
                    chunk["source"] = chunk[alt]
                    break
            else:
                chunk["source"] = "Unknown"

        predicate_counter.update(chunk["predicate"].value_counts().to_dict())

        # Explode source on chunk
        chunk_exp = chunk.copy()
        chunk_exp["source"] = chunk_exp["source"].fillna("").astype(str).str.split("|")
        chunk_exp = chunk_exp.explode("source")

        for (pred, src), cnt in chunk_exp.groupby(["predicate", "source"], observed=False).size().items():
            predicate_source_counter[(str(pred), str(src))] += cnt

        # Map categories
        sub_cats = chunk_exp["subject"].map(id_to_cat).fillna("Unknown")
        obj_cats = chunk_exp["object"].map(id_to_cat).fillna("Unknown")
        edge_triples = sub_cats + "-" + chunk_exp["predicate"].astype(str) + "-" + obj_cats

        for (triple, src), cnt in pd.DataFrame({"triple": edge_triples, "source": chunk_exp["source"]}).groupby(["triple", "source"]).size().items():
            schema_source_counter[(triple, src)] += cnt

    # Build predicates by source dataframe
    pred_src_df = pd.Series(predicate_source_counter).unstack(fill_value=0)
    pred_src_df.index.name = "predicate"

    # Build metagraph schema dataframe
    metagraph_df = pd.Series(schema_source_counter).unstack(fill_value=0)
    metagraph_df.index.name = "edge_schema"

    results = {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "category_counts": category_counts,
        "prefix_counts": prefix_counts,
        "categories_by_source": categories_by_source,
        "prefixes_by_source": prefixes_by_source,
        "predicate_counts": pd.Series(predicate_counter),
        "predicates_by_source": pred_src_df,
        "metagraph_schema": metagraph_df,
    }

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        pred_path = os.path.join(output_dir, "lcc_predicates.tsv")
        schema_path = os.path.join(output_dir, "metagraph_schema.tsv")
        cat_path = os.path.join(output_dir, "lcc_categories_by_source.tsv")
        pref_path = os.path.join(output_dir, "lcc_prefixes_by_source.tsv")

        pred_src_df.to_csv(pred_path, sep="\t")
        metagraph_df.to_csv(schema_path, sep="\t")
        categories_by_source.to_csv(cat_path, sep="\t")
        prefixes_by_source.to_csv(pref_path, sep="\t")
        print(f"Saved analysis tables to {output_dir}")

    return results


# =============================================================================
# 6. Visualization Utilities
# =============================================================================

def plot_graph_distributions(
    lcc_results: Dict[str, Any],
    output_dir: Optional[str] = None,
) -> None:
    """
    Generate publication-ready figures for predicate and node category distributions.
    """
    sns.set_theme(style="whitegrid", palette="muted")

    # 1. Top Node Categories
    cat_series = lcc_results["category_counts"].head(10)
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    sns.barplot(x=cat_series.values, y=cat_series.index.str.replace("biolink:", ""), ax=ax, color="#2b5c8f")
    ax.set_title("LCC Node Categories (Top 10)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Count (log scale)")
    ax.set_xscale("log")
    plt.tight_layout()
    if output_dir:
        plt.savefig(os.path.join(output_dir, "figure_node_categories.png"))
        plt.close(fig)
    else:
        plt.show()

    # 2. Top Edge Predicates
    pred_series = lcc_results["predicate_counts"].sort_values(ascending=False).head(12)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    sns.barplot(x=pred_series.values, y=pred_series.index.str.replace("biolink:", ""), ax=ax, color="#3e8e75")
    ax.set_title("LCC Edge Predicates (Top 12)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Count (log scale)")
    ax.set_xscale("log")
    plt.tight_layout()
    if output_dir:
        plt.savefig(os.path.join(output_dir, "figure_edge_predicates.png"))
        plt.close(fig)
    else:
        plt.show()


# =============================================================================
# 7. CLI Entrypoint
# =============================================================================

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="graph_analysis.py",
        description="Comprehensive analysis and reporting tool for ngest Knowledge Graphs.",
    )
    parser.add_argument(
        "--lcc",
        default="data/processed/finals/lcc.tar.gz",
        help="Path to LCC archive or nodes/edges directory. Default: data/processed/finals/lcc.tar.gz",
    )
    parser.add_argument(
        "--stats",
        default="data/processed/finals/merged_graph_stats.yaml",
        help="Path to merged_graph_stats.yaml metadata file.",
    )
    parser.add_argument(
        "--config",
        default="config/databases_config.yaml",
        help="Path to databases_config.yaml. Default: config/databases_config.yaml",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="data/processed/finals/analysis",
        help="Output directory for generated tables and figures. Default: data/processed/finals/analysis",
    )
    parser.add_argument(
        "--plots",
        action="store_true",
        help="Generate publication-ready figures.",
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    print("=" * 60)
    print("ngest Graph Analysis & Reporting Engine")
    print("=" * 60)

    # 1. Merged Stats YAML Analysis
    if os.path.exists(args.stats):
        print(f"\n[1/3] Parsing merged graph stats: {args.stats}")
        stats_summary = analyze_merged_stats_yaml(args.stats)
        print(f"  Total Merged Nodes: {stats_summary['total_nodes']:,}")
        print(f"  Total Merged Edges: {stats_summary['total_edges']:,}")
        stats_summary["predicates_by_source"].to_csv(
            os.path.join(args.output_dir, "merged_predicates_by_source.tsv"), sep="\t"
        )
        stats_summary["categories_by_source"].to_csv(
            os.path.join(args.output_dir, "merged_categories_by_source.tsv"), sep="\t"
        )

    # 2. LCC Deep Analysis
    if os.path.exists(args.lcc):
        print(f"\n[2/3] Analyzing Largest Connected Component: {args.lcc}")
        lcc_results = analyze_lcc_graph(args.lcc, output_dir=args.output_dir)
        print(f"  LCC Nodes: {lcc_results['total_nodes']:,}")
        print(f"  LCC Edges: {lcc_results['total_edges']:,}")

        # 3. Plots
        if args.plots:
            print(f"\n[3/3] Generating figures in: {args.output_dir}")
            plot_graph_distributions(lcc_results, output_dir=args.output_dir)
    else:
        print(f"Warning: LCC source not found at {args.lcc}")

    print("\nAnalysis completed successfully!")


if __name__ == "__main__":
    main()
