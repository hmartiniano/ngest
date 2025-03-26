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

    """
    parser = argparse.ArgumentParser(
        prog="bgee_to_kgx.py",
        description="bgee_to_csv: convert an bgee file to CSVs with nodes and edges.",
    )
    parser.add_argument("-i", "--input", help="Input files")
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
        2. Prepare data
        3. Create edge files
        4. Create node files
        5. Write files to disk.
    """
    # 1. Read input files
    parser = get_parser()
    args = parser.parse_args()
    bgee = read_files(args.input)

    # 2. Prepare data

    # Filter for rows where 'Expression' is 'present', removes 'absent' values
    bgee = bgee[bgee["Expression"].isin(["present"])]
    # Create 'object' column from 'Anatomical entity ID'
    bgee["object"] = bgee["Anatomical entity ID"]
    # Create 'subject' column with 'ENSEMBL:' prefix, it will be a Gene to be consistent with other resources
    bgee["subject"] = "ENSEMBL:" + bgee["Gene ID"]
    # Add 'provided_by' column, source of the information
    bgee["provided_by"] = "BGEE"
    # Remove rows where object column contains '∩', these are complex annotations that cannot be easily parsed
    bgee = bgee[~bgee["object"].str.contains("∩", na=False)]

    # Add 'source' and 'source version', needed for KGX
    bgee["source"] = "BGEE"
    url = args.input.split("/")[-1]
    bgee["source version"] = url.split("_")[1] + "_" + url.split("_")[2]

    # 3. Create edge files

    # Create edge file: gene_to_ae (gene to anatomical entity)
    gene_to_ae = bgee
    # Add KGX properties
    gene_to_ae["category"] = "biolink:GeneToExpressionSiteAssociation"
    gene_to_ae["predicate"] = "biolink:expressed_in"
    gene_to_ae["relation"] = "RO:0002206"
    gene_to_ae["knowledge_source"] = "BGEE"

    # Select necessary columns 
    gene_to_ae = gene_to_ae[
        [
            "subject",
            "predicate",
            "object",
            "category",
             "relation",
             "knowledge_source",
             "source",
             "source version",
        ]
    ].drop_duplicates()
    
    # Create a unique uuid for each edge
    gene_to_ae["id"] = gene_to_ae["subject"].apply(lambda x: uuid.uuid4())
    
    # 5. Write files to disk.
    # Write edges file to disk.
    gene_to_ae.to_csv(f"{args.output[1]}", sep="\t", index=False)

    # 4. Create node files

    # Create node file: anatomical entities, filter the needed columns.
    ae = bgee[
        ["object", "Anatomical entity name", "provided_by", "source", "source version"]
    ]
    
    # Create node file: anatomical entities

    # Add id, name and category columns.
    # id: The identifier of the node (anatomical entity ID).
    # name: The name of the anatomical entity.
    # category: The Biolink category of the node.
    ae["id"] = ae["object"]
    ae["name"] = ae["Anatomical entity name"]

    # Add the correct category based on the source
    # UBERON: biolink:AnatomicalEntity
    # CL: biolink:Cell
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

    # 5. Write files to disk.
    # Write nodes file to disk
    nodes[["id", "name", "category", "provided_by", "source", "source version"]].to_csv(
        f"{args.output[0]}", sep="\t", index=False
    ) 


if __name__ == "__main__":
    main()
