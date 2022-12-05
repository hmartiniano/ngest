#!/usr/bin/env python
import pandas as pd
"""
This script processes tsv files from kgx for import into neo4j using the neo4j-admin tool.
"""


def process_nodes(fname):
    df = pd.read_csv(fname, sep="\t", low_memory=False)
    print(df.columns)
    df = df.rename(columns={
        "category": ":LABEL",
        "id": ":ID",
        })
    print(df.columns)
    df[":LABEL"] = df[":LABEL"] + "|biolink:NamedThing"
    df.to_csv("nodes.csv.gz", index=False)


def process_edges(fname):
    df = pd.read_csv(fname, sep="\t", low_memory=False)
    print(df.columns)
    df = df.rename(columns={
        "predicate": ":TYPE",
        "subject": ":START_ID",
        "object": ":END_ID",
        })
    print(df.columns)
    df[":TYPE"] = df[":TYPE"] + "|" + df["category"] 
    df = df.drop(columns=["category"]
    df.to_csv("edges.csv.gz", index=False)


def main(nodes, edges):
    process_nodes(nodes)
    process_edges(edges)


if __name__ == "__main__":
    import argparse
    import sys
    main(sys.argv[1], sys.argv[2])
