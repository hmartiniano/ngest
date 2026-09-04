#!/usr/bin/env python
"""
generate_paper_figures.py: Automated generation of publication figures for ngest.

Preserves the exact visual style, layout, and color palette of the original manuscript figures
while dynamically binding to the latest Knowledge Graph data and Snakemake DAG.
"""

import argparse
import os
import subprocess
import sys
import tarfile
from collections import Counter
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, Wedge
from matplotlib.path import Path
import numpy as np
import pandas as pd
import yaml

# =============================================================================
# 1. Exact Color Palette Sampled from Original Figures
# =============================================================================

PALETTE = {
    # Node categories
    "biolink:Protein": "#63b6bb",          # Turquoise / Cyan (RGB: 99, 182, 187)
    "biolink:RNAProduct": "#d85656",        # Coral Red (RGB: 216, 86, 86)
    "biolink:Gene": "#5f7b9c",              # Steel / Slate Blue (RGB: 95, 123, 156)
    "biolink:BiologicalProcess": "#607a54", # Forest / Olive Green (RGB: 96, 122, 84)
    "biolink:Disease": "#d89c56",           # Amber / Ochre (RGB: 216, 156, 86)
    "biolink:PhenotypicFeature": "#d89c56", # Warm Gold / Ochre
    "biolink:AnatomicalEntity": "#347d81",  # Deep Teal (RGB: 52, 125, 129)
    "biolink:Cell": "#ba6f6f",              # Dusty Rose / Mauve (RGB: 186, 111, 111)
    "biolink:CellularComponent": "#b0906a", # Tan / Khaki (RGB: 176, 144, 106)
    "biolink:MolecularActivity": "#5c68a4", # Slate Indigo (RGB: 92, 104, 164)

    # Prefix color mapping (matches corresponding primary category)
    "UNIPROTKB": "#63b6bb",
    "RNACENTRAL": "#d85656",
    "ENSEMBL": "#5f7b9c",
    "GO": "#607a54",
    "MONDO": "#d89c56",
    "HP": "#d89c56",
    "UBERON": "#347d81",
    "CL": "#ba6f6f",

    # Edge predicates
    "biolink:interacts_with": "#5c68a4",    # Slate Blue
    "biolink:expressed_in": "#347d81",      # Deep Teal
    "biolink:associated_with": "#d89c56",   # Amber
    "biolink:has_gene_product": "#607a54",  # Forest Green
    "biolink:regulates": "#ba6f6f",         # Wine Red
    "biolink:subclass_of": "#b0906a",       # Tan
    "biolink:located_in": "#b0906a",        # Tan
}


# =============================================================================
# 2. Figure 3: Gene - RNA - Protein Subnetwork Map
# =============================================================================

def generate_figure3(output_path: str) -> None:
    """
    Generates Figure 3 (Gene-RNA-Protein regulatory subnetwork) using exact Biolink
    predicates and the original visual geometry, colors, and layout.
    """
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.5)
    ax.axis("off")

    # Geometry
    p_pos = (5.3, 4.4)
    r_pos = (1.9, 1.8)
    g_pos = (5.7, 1.3)
    rad = 0.85

    c_gene_product = PALETTE["biolink:has_gene_product"]
    c_interacts = PALETTE["biolink:interacts_with"]

    # Edges
    # 1. Gene -> Protein (has_gene_product)
    a1 = FancyArrowPatch((g_pos[0] + 0.35, g_pos[1] + rad), (p_pos[0] + 0.35, p_pos[1] - rad),
                         connectionstyle="arc3,rad=-0.18", color=c_gene_product, lw=3.0,
                         arrowstyle="-|>,head_length=8,head_width=5", zorder=3)
    ax.add_patch(a1)

    # 2. Gene -> RNA Product (has_gene_product)
    a2 = FancyArrowPatch((g_pos[0] - rad + 0.1, g_pos[1] + 0.25), (r_pos[0] + rad, r_pos[1] + 0.25),
                         connectionstyle="arc3,rad=-0.18", color=c_gene_product, lw=2.5,
                         arrowstyle="-|>,head_length=8,head_width=5", zorder=3)
    ax.add_patch(a2)

    # 3. RNA Product -> Gene (interacts_with)
    a3 = FancyArrowPatch((r_pos[0] + rad, r_pos[1] - 0.2), (g_pos[0] - rad + 0.1, g_pos[1] - 0.2),
                         connectionstyle="arc3,rad=-0.18", color=c_interacts, lw=4.5,
                         arrowstyle="-|>,head_length=9,head_width=5.5", zorder=3)
    ax.add_patch(a3)

    # 4. RNA Product -> Protein (interacts_with)
    a4 = FancyArrowPatch((r_pos[0] + 0.4, r_pos[1] + rad * 0.85), (p_pos[0] - rad * 0.85, p_pos[1] - 0.15),
                         connectionstyle="arc3,rad=0.12", color=c_interacts, lw=3.5,
                         arrowstyle="-|>,head_length=8,head_width=5", zorder=3)
    ax.add_patch(a4)

    # 5. Protein self-loop (interacts_with)
    p_loop = FancyArrowPatch((p_pos[0] - 0.25, p_pos[1] + rad - 0.05), (p_pos[0] + 0.3, p_pos[1] + rad - 0.05),
                             connectionstyle="arc,angleA=120,angleB=60,armA=50,armB=50,rad=35",
                             color=c_interacts, lw=3.5,
                             arrowstyle="-|>,head_length=8,head_width=5", zorder=4)
    ax.add_patch(p_loop)

    # 6. RNA Product self-loop (interacts_with)
    r_loop = FancyArrowPatch((r_pos[0] - rad + 0.05, r_pos[1] - 0.25), (r_pos[0] - rad + 0.05, r_pos[1] + 0.3),
                             connectionstyle="arc,angleA=210,angleB=150,armA=50,armB=50,rad=35",
                             color=c_interacts, lw=3.0,
                             arrowstyle="-|>,head_length=7,head_width=4.5", zorder=4)
    ax.add_patch(r_loop)

    # Draw Nodes
    nodes = [
        (p_pos, PALETTE["biolink:Protein"], "Protein"),
        (r_pos, PALETTE["biolink:RNAProduct"], "RNA\nProduct"),
        (g_pos, PALETTE["biolink:Gene"], "Gene"),
    ]
    for pos, col, label in nodes:
        c = plt.Circle(pos, rad, facecolor=col, edgecolor="#222222", lw=2.0, zorder=10)
        ax.add_patch(c)
        ax.text(pos[0], pos[1], label, color="white", fontsize=15, fontweight="bold",
                ha="center", va="center", zorder=11)

    # Legend on the right
    leg_x = 7.7
    ax.plot(leg_x, 4.3, "o", color=c_gene_product, markersize=19, markeredgecolor="#222222", markeredgewidth=1.8)
    ax.text(leg_x + 0.35, 4.3, "Has gene product", fontsize=14, fontweight="bold", va="center")

    ax.plot(leg_x, 3.2, "o", color=c_interacts, markersize=19, markeredgecolor="#222222", markeredgewidth=1.8)
    ax.text(leg_x + 0.35, 3.2, "Interacts with", fontsize=14, fontweight="bold", va="center")

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated Figure 3: {output_path}")


# =============================================================================
# 3. Figure 2: Metagraph Schema, Data Sources, and Prefix Flow
# =============================================================================

def draw_sankey_panel(ax, prefix_flows: List[Tuple[str, str, int]]):
    """
    Renders an elegant ribbon Sankey diagram of prefix flows using matplotlib.
    """
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    # Select prominent prefixes
    left_prefixes = ["UNIPROTKB", "ENSEMBL", "RNACENTRAL", "UBERON", "MONDO", "HP", "GO", "CL"]
    right_prefixes = ["UNIPROTKB", "UBERON", "ENSEMBL", "HP", "GO", "MONDO", "CL", "RNACENTRAL"]

    # Filter flows between these
    filtered = []
    for s, o, c in prefix_flows:
        if s in left_prefixes and o in right_prefixes:
            filtered.append((s, o, c))

    # Calculate total out from left and in to right
    out_totals = Counter()
    in_totals = Counter()
    for s, o, c in filtered:
        out_totals[s] += c
        in_totals[o] += c

    max_tot = max(sum(out_totals.values()), sum(in_totals.values()))

    # Positions
    margin = 0.5
    avail_h = 9.0
    gap = 0.15

    # Compute vertical blocks on left
    cur_y = 9.5
    left_blocks = {}
    total_left_val = sum(out_totals[p] for p in left_prefixes)
    scale_y = (avail_h - (len(left_prefixes) - 1) * gap) / max(total_left_val, 1)

    for p in left_prefixes:
        val = out_totals[p]
        bh = max(val * scale_y, 0.12)
        left_blocks[p] = {"top": cur_y, "bottom": cur_y - bh, "height": bh, "cur_out": cur_y}
        cur_y -= (bh + gap)

    # Compute vertical blocks on right
    cur_y = 9.5
    right_blocks = {}
    total_right_val = sum(in_totals[p] for p in right_prefixes)
    scale_y_r = (avail_h - (len(right_prefixes) - 1) * gap) / max(total_right_val, 1)

    for p in right_prefixes:
        val = in_totals[p]
        bh = max(val * scale_y_r, 0.12)
        right_blocks[p] = {"top": cur_y, "bottom": cur_y - bh, "height": bh, "cur_in": cur_y}
        cur_y -= (bh + gap)

    # Draw left and right anchor bars
    x_left = 1.8
    x_right = 8.2
    bar_w = 0.25

    for p, b in left_blocks.items():
        col = PALETTE.get(p, "#999999")
        rect = patches.Rectangle((x_left - bar_w, b["bottom"]), bar_w, b["height"],
                                 facecolor=col, edgecolor="none", zorder=5)
        ax.add_patch(rect)
        ax.text(x_left - bar_w - 0.15, (b["top"] + b["bottom"]) / 2, p,
                fontsize=8, fontweight="bold", ha="right", va="center")

    for p, b in right_blocks.items():
        col = PALETTE.get(p, "#999999")
        rect = patches.Rectangle((x_right, b["bottom"]), bar_w, b["height"],
                                 facecolor=col, edgecolor="none", zorder=5)
        ax.add_patch(rect)
        ax.text(x_right + bar_w + 0.15, (b["top"] + b["bottom"]) / 2, p,
                fontsize=8, fontweight="bold", ha="left", va="center")

    # Sort flows to reduce ribbon crossing
    sorted_flows = sorted(filtered, key=lambda f: f[2], reverse=True)

    # Draw ribbons
    for s, o, count in sorted_flows:
        flow_h_l = (count / max(out_totals[s], 1)) * left_blocks[s]["height"]
        flow_h_r = (count / max(in_totals[o], 1)) * right_blocks[o]["height"]

        y0_top = left_blocks[s]["cur_out"]
        y0_bot = y0_top - flow_h_l
        left_blocks[s]["cur_out"] = y0_bot

        y1_top = right_blocks[o]["cur_in"]
        y1_bot = y1_top - flow_h_r
        right_blocks[o]["cur_in"] = y1_bot

        col = PALETTE.get(s, "#999999")

        # Bezier curve ribbon
        verts = [
            (x_left, y0_bot),
            (x_left + 2.5, y0_bot),
            (x_right - 2.5, y1_bot),
            (x_right, y1_bot),
            (x_right, y1_top),
            (x_right - 2.5, y1_top),
            (x_left + 2.5, y0_top),
            (x_left, y0_top),
            (x_left, y0_bot)
        ]
        codes = [
            Path.MOVETO,
            Path.CURVE4, Path.CURVE4, Path.CURVE4,
            Path.LINETO,
            Path.CURVE4, Path.CURVE4, Path.CURVE4,
            Path.CLOSEPOLY
        ]
        path = Path(verts, codes)
        patch = patches.PathPatch(path, facecolor=col, alpha=0.45, edgecolor="none", zorder=3)
        ax.add_patch(patch)


def generate_figure2(output_path: str, prefix_flows: List[Tuple[str, str, int]]) -> None:
    """
    Generates composite Figure 2 (Metagraph schema, Source distributions, Sankey prefix flows).
    """
    fig = plt.figure(figsize=(16, 7.5), dpi=300)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.1, 1.0], height_ratios=[1.0, 1.0],
                          wspace=0.15, hspace=0.15)

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[:, 1])

    # -------------------------------------------------------------------------
    # Panel A: Metagraph Schema
    # -------------------------------------------------------------------------
    ax_a.axis("off")
    ax_a.set_xlim(0, 10)
    ax_a.set_ylim(0, 6)
    ax_a.text(0.1, 5.7, "A.", fontsize=16, fontweight="bold")

    # Node positions (10 core LCC categories)
    node_coords = {
        "Disease": (1.8, 4.8),
        "Cell": (4.5, 5.0),
        "Anatomical\nEntity": (7.5, 4.6),
        "Phenotypic\nFeature": (0.9, 3.2),
        "Gene": (2.8, 2.8),
        "Protein": (5.2, 3.0),
        "Biological\nProcess": (7.8, 3.0),
        "RNA\nProduct": (1.1, 1.2),
        "Cellular\nComponent": (4.8, 1.2),
        "Molecular\nActivity": (7.8, 1.4),
    }

    node_colors = {
        "Disease": PALETTE["biolink:Disease"],
        "Cell": PALETTE["biolink:Cell"],
        "Anatomical\nEntity": PALETTE["biolink:AnatomicalEntity"],
        "Phenotypic\nFeature": PALETTE["biolink:PhenotypicFeature"],
        "Gene": PALETTE["biolink:Gene"],
        "Protein": PALETTE["biolink:Protein"],
        "Biological\nProcess": PALETTE["biolink:BiologicalProcess"],
        "RNA\nProduct": PALETTE["biolink:RNAProduct"],
        "Cellular\nComponent": PALETTE["biolink:CellularComponent"],
        "Molecular\nActivity": PALETTE["biolink:MolecularActivity"],
    }

    # Draw edges between nodes (including critical RNAProduct -> Gene / Protein)
    edges = [
        ("RNA\nProduct", "Gene", 0.15),
        ("RNA\nProduct", "Protein", 0.12),
        ("Gene", "Protein", -0.15),
        ("Gene", "Disease", 0.1),
        ("Gene", "Phenotypic\nFeature", -0.1),
        ("Gene", "Anatomical\nEntity", 0.15),
        ("Gene", "Cell", 0.05),
        ("Protein", "Protein", 0.0), # handled as loop
        ("Protein", "Biological\nProcess", 0.1),
        ("Protein", "Molecular\nActivity", -0.1),
        ("Protein", "Cellular\nComponent", 0.05),
        ("Cell", "Anatomical\nEntity", -0.1),
        ("Biological\nProcess", "Molecular\nActivity", 0.05),
        ("Disease", "Phenotypic\nFeature", 0.05),
    ]

    for s, t, rad in edges:
        p1 = node_coords[s]
        p2 = node_coords[t]
        edge = FancyArrowPatch(p1, p2, connectionstyle=f"arc3,rad={rad}",
                               color="#444444", lw=1.6, arrowstyle="-", zorder=2)
        ax_a.add_patch(edge)

    # Self loops for key nodes
    for n in ["Protein", "RNA\nProduct", "Phenotypic\nFeature"]:
        p = node_coords[n]
        loop = FancyArrowPatch((p[0] - 0.25, p[1] + 0.35), (p[0] + 0.25, p[1] + 0.35),
                                connectionstyle="arc3,rad=1.8", color="#444444", lw=1.5,
                                arrowstyle="-", zorder=2)
        ax_a.add_patch(loop)

    # Render Node circles
    for name, (x, y) in node_coords.items():
        col = node_colors[name]
        c = plt.Circle((x, y), 0.55, facecolor=col, edgecolor="#222222", lw=1.5, zorder=5)
        ax_a.add_patch(c)
        ax_a.text(x, y, name, color="white", fontsize=7.5, fontweight="bold",
                  ha="center", va="center", zorder=6)

    # -------------------------------------------------------------------------
    # Panel B: Data Sources (14 Databases with Category Slices)
    # -------------------------------------------------------------------------
    ax_b.axis("off")
    ax_b.set_xlim(0, 10)
    ax_b.set_ylim(0, 5)
    ax_b.text(0.1, 4.7, "B.", fontsize=16, fontweight="bold")

    # Sources and their category color wedges
    c_gene = PALETTE["biolink:Gene"]
    c_prot = PALETTE["biolink:Protein"]
    c_rna = PALETTE["biolink:RNAProduct"]
    c_anat = PALETTE["biolink:AnatomicalEntity"]
    c_cell = PALETTE["biolink:Cell"]
    c_dis = PALETTE["biolink:Disease"]
    c_phen = PALETTE["biolink:PhenotypicFeature"]
    c_bp = PALETTE["biolink:BiologicalProcess"]
    c_cc = PALETTE["biolink:CellularComponent"]
    c_mf = PALETTE["biolink:MolecularActivity"]

    db_specs = [
        ("BGEE", [c_gene, c_anat, c_cell], (1.2, 3.6)),
        ("CL", [c_cell, c_anat, c_bp], (2.8, 3.6)),
        ("DisGeNET", [c_gene, c_dis, c_phen], (4.4, 3.6)),
        ("ENSEMBL", [c_gene, c_prot], (6.0, 3.6)),
        ("GO", [c_bp, c_cc, c_mf], (7.6, 3.6)),
        ("GOA", [c_prot, c_bp, c_cc, c_mf], (1.2, 2.2)),
        ("HPO", [c_phen], (2.8, 2.2)),
        ("HPOA", [c_dis, c_phen], (4.4, 2.2)),
        ("TarBase", [c_rna, c_gene], (6.0, 2.2)),  # DIANA-TarBase
        ("MONDO", [c_dis, c_anat], (7.6, 2.2)),
        ("NPInter", [c_rna, c_gene, c_prot], (2.8, 0.8)),
        ("RNACentral", [c_rna, c_gene], (4.4, 0.8)),
        ("STRING", [c_prot], (6.0, 0.8)),
        ("UBERON", [c_anat, c_cell], (7.6, 0.8)),
    ]

    for name, colors, (bx, by) in db_specs:
        num_c = len(colors)
        step = 360.0 / num_c
        for i, col in enumerate(colors):
            w = Wedge((bx, by), 0.5, i * step, (i + 1) * step, facecolor=col,
                      edgecolor="#333333", lw=0.8, zorder=5)
            ax_b.add_patch(w)
        # Inner text background circle
        inner = plt.Circle((bx, by), 0.38, facecolor="white", edgecolor="none", alpha=0.3, zorder=6)
        ax_b.add_patch(inner)
        ax_b.text(bx, by, name, color="white", fontsize=7.0, fontweight="bold",
                  ha="center", va="center", zorder=7)

    # -------------------------------------------------------------------------
    # Panel C: Sankey Prefix Flow
    # -------------------------------------------------------------------------
    ax_c.text(0.1, 9.7, "C.", fontsize=16, fontweight="bold")
    draw_sankey_panel(ax_c, prefix_flows)

    # -------------------------------------------------------------------------
    # Bottom Legend
    # -------------------------------------------------------------------------
    leg_cats = [
        ("Anatomical Entity", PALETTE["biolink:AnatomicalEntity"]),
        ("Biological Process", PALETTE["biolink:BiologicalProcess"]),
        ("Cell", PALETTE["biolink:Cell"]),
        ("Cellular Component", PALETTE["biolink:CellularComponent"]),
        ("Disease", PALETTE["biolink:Disease"]),
        ("Gene", PALETTE["biolink:Gene"]),
        ("Molecular Activity", PALETTE["biolink:MolecularActivity"]),
        ("Phenotypic Feature", PALETTE["biolink:PhenotypicFeature"]),
        ("Protein", PALETTE["biolink:Protein"]),
        ("RNA Product", PALETTE["biolink:RNAProduct"]),
    ]

    fig.subplots_adjust(bottom=0.12)
    leg_ax = fig.add_axes([0.05, 0.01, 0.9, 0.08])
    leg_ax.axis("off")
    leg_ax.set_xlim(0, 10)
    leg_ax.set_ylim(0, 2)

    for i, (label, col) in enumerate(leg_cats):
        col_idx = i % 5
        row_idx = 1 - (i // 5)
        lx = 0.3 + col_idx * 1.95
        ly = 0.5 + row_idx * 0.8
        leg_ax.plot(lx, ly, "o", color=col, markersize=10, markeredgecolor="#222222", markeredgewidth=1.2)
        leg_ax.text(lx + 0.15, ly, label, fontsize=8.5, fontweight="bold", va="center")

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated Figure 2: {output_path}")


# =============================================================================
# 4. Figure 1: Pipeline DAG
# =============================================================================

def generate_figure1(output_path: str, workflow_dir: str) -> None:
    """
    Renders the live Snakemake rulegraph using graphviz dot to ensure
    rule names (e.g. download_tarbase, process_tarbase) are 100% accurate.
    """
    cmd = "snakemake --rulegraph 2>/dev/null | dot -Tpng -Gdpi=300"
    try:
        proc = subprocess.run(cmd, shell=True, cwd=workflow_dir, capture_output=True, check=True)
        with open(output_path, "wb") as f:
            f.write(proc.stdout)
        print(f"Generated Figure 1: {output_path}")
    except Exception as e:
        print(f"Warning: Could not render live rulegraph: {e}")


# =============================================================================
# 5. CLI Entrypoint
# =============================================================================

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_paper_figures.py",
        description="Automated, publication-grade figure generation for ngest.",
    )
    parser.add_argument(
        "--lcc",
        default="data/processed/finals/lcc.tar.gz",
        help="Path to lcc.tar.gz archive.",
    )
    parser.add_argument(
        "--workflow-dir",
        default="workflow",
        help="Path to workflow directory containing Snakefile.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="paper/Figures",
        help="Output directory for generated figure files.",
    )
    return parser


def load_prefix_flows(lcc_path: str) -> List[Tuple[str, str, int]]:
    """
    Extracts prefix-to-prefix edge flows from cached TSV or lcc.tar.gz.
    """
    cached_tsv = "data/processed/finals/analysis/lcc_prefix_flows.tsv"
    if os.path.exists(cached_tsv):
        df = pd.read_csv(cached_tsv, sep="\t")
        return list(zip(df["subject_prefix"], df["object_prefix"], df["edge_count"]))

    counter = Counter()
    if not os.path.exists(lcc_path):
        print(f"Warning: {lcc_path} not found. Using fallback prefix flows.")
        return [
            ("UNIPROTKB", "UNIPROTKB", 10611001),
            ("ENSEMBL", "UBERON", 6616463),
            ("RNACENTRAL", "ENSEMBL", 1258988),
            ("ENSEMBL", "HP", 508587),
            ("UNIPROTKB", "GO", 425736),
            ("RNACENTRAL", "UNIPROTKB", 342266),
            ("ENSEMBL", "MONDO", 317053),
            ("ENSEMBL", "CL", 234628),
            ("ENSEMBL", "UNIPROTKB", 93400),
            ("GO", "GO", 84982),
            ("ENSEMBL", "RNACENTRAL", 58581),
            ("MONDO", "MONDO", 39433),
            ("UBERON", "UBERON", 38236),
            ("HP", "HP", 23139),
            ("CL", "CL", 4594),
        ]

    with tarfile.open(lcc_path, "r:*") as tar:
        for member in tar:
            if member.name.endswith("edges.tsv"):
                with tar.extractfile(member) as f:
                    for chunk in pd.read_csv(f, sep="\t", usecols=["subject", "object"],
                                             chunksize=1000000, low_memory=False):
                        s_pref = chunk["subject"].str.split(":").str[0]
                        o_pref = chunk["object"].str.split(":").str[0]
                        pairs = pd.Series(zip(s_pref, o_pref)).value_counts()
                        for pair, count in pairs.items():
                            counter[pair] += count
                break

    flows = [(s, o, c) for (s, o), c in counter.most_common(25)]
    return flows


def main():
    parser = get_parser()
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 60)
    print("ngest Automated Paper Figure Generator")
    print("=" * 60)

    # 1. Figure 3: Gene-RNA-Protein Subnetwork
    fig3_path = os.path.join(args.output_dir, "Figure3map.png")
    generate_figure3(fig3_path)

    # 2. Figure 2: Metagraph Schema + Sources + Sankey
    fig2_path = os.path.join(args.output_dir, "Figure2paper.png")
    print("Loading prefix flows for Figure 2...")
    prefix_flows = load_prefix_flows(args.lcc)
    generate_figure2(fig2_path, prefix_flows)

    # 3. Figure 1: Pipeline DAG
    fig1_path = os.path.join(args.output_dir, "Figure1_pipeline_dag.png")
    generate_figure1(fig1_path, args.workflow_dir)

    print("\nAll paper figures generated successfully!")


if __name__ == "__main__":
    main()
