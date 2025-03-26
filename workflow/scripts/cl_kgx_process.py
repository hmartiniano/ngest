""" 
This script processes Cell Ontology (CL) data from KGX files.

It maps CL IDs to UniProt IDs and outputs the transformed data into new KGX-compliant files.
"""
import argparse
import pandas as pd
import requests

# URL to fetch the latest CL release version from GitHub
release = "https://api.github.com/repos/obophenotype/cell-ontology/releases/latest"


def get_parser():
    """
    Creates and configures an argument parser for command-line input.

    Returns:
        argparse.ArgumentParser: The argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="cl_kgx_process.py",
        description="cl_kgx_process: convert protein ids from cl kgx files.",
    )
    parser.add_argument(
        "-i", "--input", nargs="+", help="Input files (clnodes and cledges)"
    )
    parser.add_argument(
        "-m", "--mapping", help="Input mapping file (CL to external IDs)"
    )
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default="cl",
        help="Output prefix for nodes and edges files. Default: cl",
    )
    return parser


def main():
    """
    Main function to process CL data, map IDs, and output transformed data.

    This function performs the following steps:
    1. Parses command-line arguments.
    2. Loads CL nodes, edges, and mapping data from input files.
    3. Fetches the latest CL release version from GitHub.
    4. Adds source and version information to nodes and edges.
    5. Filters the mapping file for UniProt cross-references.
    6. Maps CL IDs to UniProt IDs in nodes and edges.
    7. Replaces original CL IDs with UniProt IDs where available.
    8. Removes nodes and edges associated with PR (protein region) IDs.
    9. Outputs the transformed nodes and edges to TSV files.
    """
    # 1. Parse command-line arguments.
    parser = get_parser()
    args = parser.parse_args()

    # 2. Load input files into pandas DataFrames.
    clnodes = pd.read_csv(args.input[0], sep="\t", low_memory=False)
    cledges = pd.read_csv(args.input[1], sep="\t", low_memory=False)
    clmapping = pd.read_csv(args.mapping, sep="\t", header=None, low_memory=False)

    # 3. Fetch the latest CL release version from GitHub.
    response = requests.get(release)
    version = response.json()["name"]

    # 4. Add source and version information to nodes.
    clnodes["source"] = "CL"
    clnodes["source version"] = version

    # Add source and version information to edges.
    cledges["source"] = "CL"
    cledges["source version"] = version

    # 5. Process the mapping file:
    # Set column names for the mapping file.
    clmapping.columns = ["ID", "xref", "Relation"]

    # Filter the mapping file to only include rows with UniProt in the xref column.
    # Keep only the ID and xref columns, removing duplicates.
    clmapping = (
        clmapping[clmapping["xref"].str.contains("UniProt")][["ID", "xref"]]
        .drop_duplicates()
        .set_index("ID")
    )
    # Remove duplicated IDs, keeping the first, and select only the xref column.
    clmapping = clmapping[~clmapping.index.duplicated(keep="first")].iloc[:, 0]

    # 6. Map CL IDs to UniProt IDs in nodes and edges.
    # Transform nodes: add Uniprot ID column.
    clnodes["Uniprot ID"] = (
        "UNIPROTKB:" + clnodes["id"].map(clmapping).str.split(":").str[-1]
    )
    # Transform edges: add Object Uniprot ID column.
    cledges["Object Uniprot ID"] = (
        "UNIPROTKB:" + cledges["object"].map(clmapping).str.split(":").str[-1]
    )
    # Transform edges: add Subject Uniprot ID column.
    cledges["Subject Uniprot ID"] = (
        "UNIPROTKB:" + cledges["subject"].map(clmapping).str.split(":").str[-1]
    )

    # 7. Replace original IDs with UniProt IDs if available. 
    # Fill in any missing values from the right.
    # Transform nodes: update id column.
    clnodes["id"] = clnodes[["Uniprot ID", "id"]].bfill(axis=1).iloc[:, 0]
    # Transform edges: update object column.
    cledges["object"] = (
        cledges[["Object Uniprot ID", "object"]].bfill(axis=1).iloc[:, 0]
    )
    # Transform edges: update subject column.
    cledges["subject"] = (
        cledges[["Subject Uniprot ID", "subject"]].bfill(axis=1).iloc[:, 0]
    )
    # 8. Remove nodes where ID starts with PR (protein region)
    clnodes = clnodes[~clnodes.id.str.startswith("PR")]
    # output clnodes to file.
    clnodes[
        ["id", "category", "name", "provided_by", "source", "source version"]
    ].drop_duplicates().to_csv(f"{args.output[0]}_nodes.tsv", sep="\t", index=False)

    # Remove edges where subject or object start with PR
    # 8. Remove edges where subject or object start with PR (protein region).
    cledges = cledges[~cledges.subject.str.startswith("PR")]
    cledges = cledges[~cledges.object.str.startswith("PR")]
    # 9. Output cledges to file.
    cledges[
        [
            "id",  # Edge ID
            "subject",  # Subject node
            "predicate",  # Edge type
            "object",  # Object node
            "relation",  # Relation
            "knowledge_source",  # Knowledge source
            "source",  # source name
            "source version",  # source version
        ]
    ].to_csv(f"{args.output[1]}_edges.tsv", sep="\t", index=False)


if __name__ == "__main__":
    main()
