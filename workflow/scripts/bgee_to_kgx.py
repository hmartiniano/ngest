import argparse
import pandas as pd
import uuid


"""
This script processes Bgee data to create KGX (Knowledge Graph Exchange) compliant node and edge files.
It reads a Bgee TSV file, filters it, transforms the data into nodes and edges,
and then writes them to separate TSV files.

The output files are a nodes file and an edges file, both formatted as TSVs following the KGX schema.
"""

def read_files(fname):
    """
    Reads a tab-separated file into a pandas DataFrame.
    
    This function takes a file path as input and reads the file content into a pandas DataFrame.
    It assumes the file is tab-separated and uses low_memory=False to avoid any potential issues with 
    large datasets.
    
    The function is designed to handle large datasets efficiently, but it might require more memory.

    Args:
        fname (str): The path to the tab-separated file.
        fname (str): The path to the CSV file.
    Returns:
        pandas.DataFrame: A pandas DataFrame containing the data from the CSV file.

    Raises:
        IOError: If the file cannot be read.
    """
    df = pd.read_csv(fname, sep="\t", low_memory=False)
    return df


def get_parser():
    """
    Configures and returns an argument parser for command-line arguments.

    This function sets up an argument parser using the `argparse` module. 
    It defines the program's name, description, and the expected command-line arguments:
    - `-i` or `--input`: The path to the input Bgee file.
    - `-o` or `--output`: The prefix for the output files (default: "bgee").

    Returns:
        argparse.ArgumentParser: An argument parser configured for this script.

    Raises:
        None

    """
    parser = argparse.ArgumentParser(
        prog="bgee_to_kgx.py",
        description="bgee_to_csv: convert a Bgee expression file to CSVs with nodes and edges.",
    )
    parser.add_argument("-i", "--input", help="Input files")
    parser.add_argument(
        "--gold-only",
        action="store_true",
        default=False,
        help="Filter to retain only 'gold quality' expression calls. Default: False",
    )
    parser.add_argument(
        "--max-fdr",
        type=float,
        default=None,
        help="Maximum FDR threshold to filter expression calls (e.g. 0.01). Default: None",
    )
    parser.add_argument(
        "-o", "--output", nargs="+", default="bgee", help="Output prefix. Default: out"
    )
    return parser


def main():
    """
    Main function to process Bgee data and generate KGX nodes and edges.
    
    The script processes the Bgee file provided through the command-line, it filters
    it to use only the "present" elements, then maps gene IDs to Ensembl IDs,
    anatomical entities IDs, and generates node and edge files in a KGX-compatible format.
    
    The process can be divided in the following steps:
        1. Read input files
        2. Filter data and Prepare for nodes and edges creation
        3. Create edge files (gene_to_ae)
        4. Create node files (anatomical entities and genes)
        5. Write files to disk (edges and nodes).

    """
    # Step 1: Read input files using the argument parser
    parser = get_parser()
    args = parser.parse_args()
    bgee = read_files(args.input)

    bgee = bgee[bgee["Expression"].isin(["present"])]

    # Optional quality and FDR filtering
    if args.gold_only and "Call quality" in bgee.columns:
        bgee = bgee[bgee["Call quality"] == "gold quality"]
    if args.max_fdr is not None and "FDR" in bgee.columns:
        bgee = bgee[bgee["FDR"] <= args.max_fdr]

    bgee["object"] = bgee["Anatomical entity ID"]
    bgee["subject"] = "ENSEMBL:" + bgee["Gene ID"]
    bgee["provided_by"] = "BGEE"
    bgee = bgee[~bgee["object"].str.contains("∩", na=False)]

    # Prepare data for edges creation:
    # Create 'object' column from 'Anatomical entity ID', this will be the target of the relation (edge).
    bgee["object"] = bgee["Anatomical entity ID"]
    # Create 'subject' column with 'ENSEMBL:' prefix, this will be the source of the relation (edge).
    # Adding the prefix makes it consistent with other resources
    bgee["subject"] = "ENSEMBL:" + bgee["Gene ID"]
    # Add 'provided_by' column, indicating the source of the information
    bgee["provided_by"] = "BGEE"

    # Add 'source' and 'source version', required in KGX
    bgee["source"] = "BGEE"
    # Retrieve the input filename from the path
    url = args.input.split("/")[-1]
    # Extract the version from the input filename (e.g., "14_2" from "file_14_2_something.tsv")
    bgee["source version"] = url.split("_")[1] + "_" + url.split("_")[2]

    gene_to_ae = bgee.copy()
    gene_to_ae["category"] = "biolink:GeneToExpressionSiteAssociation"
    gene_to_ae["predicate"] = "biolink:expressed_in"
    gene_to_ae["relation"] = "RO:0002206"
    gene_to_ae["knowledge_source"] = "BGEE"

    # Retain expression quality metrics
    if "Call quality" in gene_to_ae.columns:
        gene_to_ae["call_quality"] = gene_to_ae["Call quality"].fillna("")
    if "FDR" in gene_to_ae.columns:
        gene_to_ae["fdr"] = gene_to_ae["FDR"]
    if "Expression score" in gene_to_ae.columns:
        gene_to_ae["expression_score"] = gene_to_ae["Expression score"]
    if "Expression rank" in gene_to_ae.columns:
        gene_to_ae["expression_rank"] = gene_to_ae["Expression rank"]

    edge_cols = [
        "subject",
        "predicate",
        "object",
        "category",
        "relation",
        "call_quality",
        "fdr",
        "expression_score",
        "expression_rank",
        "knowledge_source",
        "source",
        "source version",
    ]
    # Keep only available columns
    avail_cols = [c for c in edge_cols if c in gene_to_ae.columns]
    gene_to_ae = gene_to_ae[avail_cols].drop_duplicates()
    gene_to_ae["id"] = gene_to_ae["subject"].apply(lambda x: uuid.uuid4())
    gene_to_ae.to_csv(f"{args.output[1]}", sep="\t", index=False)

    # Step 4: Create node files (anatomical entities and genes)

    # Prepare node file: anatomical entities
    # Filter the needed columns.
    ae = bgee[
        ["object", "Anatomical entity name", "provided_by", "source", "source version"]
    ]
    
    # Transform columns:
    # Add id, name and category columns.
    # id: The identifier of the node (anatomical entity ID).
    # name: The name of the anatomical entity.
    # category: The Biolink category of the node.
    ae["id"] = ae["object"]
    ae["name"] = ae["Anatomical entity name"]
    
    # Add the correct category based on the ID prefix
    # This is needed since we may have UBERON (anatomical entity) or CL (cell) entities.
    # UBERON: biolink:AnatomicalEntity
    # CL: biolink:Cell
    # This is a way to add all the values in a column with a specific condition
    ae.loc[ae["id"].str.contains("UBERON"), "category"] = "biolink:AnatomicalEntity"
    ae.loc[ae["id"].str.contains("CL"), "category"] = "biolink:Cell"

    # Create node file: genes, filter the needed columns.
    genes = bgee[["subject", "provided_by", "Gene name", "source", "source version"]]
    genes["id"] = genes["subject"]
    genes["category"] = "biolink:Gene"
    genes["name"] = genes["Gene name"]

    # Concat anatomical entities and genes into a single dataframe
    nodes = pd.concat(
        [
            genes[
                ["id", "category", "name", "provided_by", "source", "source version"]
            ],
            ae[["id", "category", "name", "provided_by", "source", "source version"]],
        ]
    ).drop_duplicates()
    
    # Step 5: Write nodes file to disk
    nodes[["id", "name", "category", "provided_by", "source", "source version"]].to_csv(
        f"{args.output[0]}", sep="\t", index=False
    )


if __name__ == "__main__":
    main()
