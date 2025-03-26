#!/usr/bin/env python
# Import necessary libraries: numpy for numerical operations and pandas for data manipulation.
import numpy as np
import pandas as pd

"""
This script processes tsv files from kgx for import into neo4j using the neo4j-admin tool.
The script takes two arguments: a nodes file and an edges file. It then converts these files into a format
that is compatible with neo4j's bulk import tool.
"""


def process_nodes(fname):
    """
    Processes a nodes file from KGX into a CSV file suitable for Neo4j import.

    Args:
        fname (str): The filename of the nodes TSV file.
    """
    # Read the TSV file into a pandas DataFrame.
    # The 'low_memory=False' argument is used to prevent potential parsing issues with large files.
    df = pd.read_csv(fname, sep="\t", low_memory=False)
    # Print the columns of the DataFrame for verification.
    print(df.columns)
    # Rename specific columns to match the required format for Neo4j import. 
    # 'category' becomes 'category:LABEL' and 'id' becomes 'id:ID'.
    df = df.rename(
        columns={
            "category": "category:LABEL",
            "id": "id:ID",
        }
    )
    # Fill in missing 'name' values with the 'id' value if 'name' is null. 
    # This ensures that every node has a name.
    df["name"] = np.where(df["name"].isnull(), df["id:ID"], df["name"])
    # Replace '|' characters in the 'xref' column with ';'.
    # This is done to properly format multiple cross-references, 
    # as Neo4j expects multiple values to be separated by semicolons.
    df["xref"] = df["xref"].str.replace("|", ";", regex=False)
    # Print the updated columns.
    print(df.columns)
    # Append ";biolink:NamedThing" to the 'category:LABEL' column. 
    # This adds a generic biolink category to all nodes. 
    # The biolink:NamedThing is a superclass of all biolink categories.
    df["category:LABEL"] = df["category:LABEL"] + ";biolink:NamedThing"
    # Save the processed DataFrame as a compressed CSV file ('nodes.csv.gz').
    df.to_csv("nodes.csv.gz", index=False)


def process_edges(fname):
    """Processes an edges file from KGX into a CSV file suitable for Neo4j import.

    Args:
        fname (str): The filename of the edges TSV file.
    """
    # Read the edges TSV file into a pandas DataFrame. 
    # The 'low_memory=False' argument is used to prevent potential parsing issues with large files.
    df = pd.read_csv(fname, sep="\t", low_memory=False)
    # Rename columns to match the required format for Neo4j import. 
    # 'predicate' becomes 'predicate:TYPE', 'subject' becomes 'subject:START_ID', 
    # and 'object' becomes 'object:END_ID'.
    df = df.rename(columns={"predicate": "predicate:TYPE", "subject": "subject:START_ID", "object": "object:END_ID",})
    # Print columns for verification.
    print(df.columns)    
    # Print the head (first few rows) of the DataFrame for verification.
    print(df.head())    
    # commented out - code to format categories into a single :TYPE string
    # df[":TYPE"] = df[":TYPE"] + ";" + df["category"]
    # df[":TYPE"] = df[":TYPE"].str.replace(";$", "", regex=True)
    print(df.head())
    # commented out - code to drop category column once :TYPE is formed
    # df = df.drop(columns=["category"])
    # Save the processed DataFrame as a compressed CSV file ('edges.csv.gz').
    df.to_csv("edges.csv.gz", index=False)


# Main function - processes nodes and edges from tsv files into a format for neo4j
def main(nodes, edges):
    """Processes the nodes and edges files."""
    # Calls the function to process the nodes file.
    process_nodes(nodes)
    # Calls the function to process the edges file.
    process_edges(edges)


if __name__ == "__main__":
    # Import the argparse library for parsing command-line arguments.
    import argparse
    # Import the sys library for getting command line arguments.
    import sys
    # Call the main function with the command line argument: sys.argv[1] nodes.tsv, sys.argv[2] edges.tsv
    main(sys.argv[1], sys.argv[2])
