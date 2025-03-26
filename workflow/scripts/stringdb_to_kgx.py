import argparse
import pandas as pd
import uuid
import logging


def read_id_mapping_uniprot(fname, id_column_name, db_type):
    """Reads and processes a UniProt ID mapping file.

    Args:
        fname (str): Path to the UniProt ID mapping file.
        id_column_name (str): The name of the column to use as the index.
        db_type (str): The type of database to filter by.

    Returns:
        pandas.Series: A Series mapping IDs from the specified column to the "Database ID".
    """
    # Read the file into a DataFrame, specifying the separator and column names.
    df = pd.read_csv(fname, sep="\t", header=None, low_memory=False)
    df.columns = ["ID", "Database", "Database ID"]
    
    # Filter the DataFrame by the specified database type.
    df = df[df["Database"] == db_type]
    
    # Clean up the "Database ID" column by splitting and taking the first part.
    df["Database ID"] = df["Database ID"].str.split("_").str[0]
    # Set the specified column as the index and drop duplicates.
    df = df[["ID", "Database ID"]].drop_duplicates().set_index(id_column_name)
    # Remove rows with duplicate indices, keeping the first occurrence.
    df = df[~df.index.duplicated(keep="first")].iloc[:, 0]
    # Return the resulting Series.
    return df


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Extract the STRING database version from the input filename.
    version = args.input.split("/")[-1]
    version = version.split(".")[3]

    # Read the STRING interactions file.
    stringdbf = pd.read_csv(args.input, sep=" ", low_memory=False)

    # Read UniProt ID mappings for STRING and UniProtKB-ID.
    idmapping = read_id_mapping_uniprot(args.proteins, "Database ID", "STRING")
    namemapping = read_id_mapping_uniprot(args.proteins, "ID", "UniProtKB-ID")

    # Map protein IDs using the ID mapping.
    stringdbf["protein1 id"] = stringdbf["protein1"].map(idmapping)
    stringdbf["protein2 id"] = stringdbf["protein2"].map(idmapping)

    # Drop rows with missing protein IDs.
    stringdbf = stringdbf.dropna(subset=["protein1 id", "protein2 id"])
    
    # Create subject and object columns.
    stringdbf["subject"] = "UNIPROTKB:" + stringdbf["protein1 id"]  # subject should be UNIPROTKB and protein1 id
    stringdbf["object"] = "UNIPROTKB:" + stringdbf["protein2 id"]  # object should be UNIPROTKB and protein2 id
    
    # Add metadata columns for edges.
    stringdbf["provided_by"] = "STRING"  # The data is provided by STRING database
    stringdbf["knowledge_source"] = "STRING"  # the source is the STRING database
    stringdbf["predicate"] = "biolink:interacts_with"
    stringdbf["relation"] = "RO:0002436"
    stringdbf["category"] = "biolink:Protein"
    stringdbf["has_confidence_level"] = stringdbf["combined_score"]
    stringdbf["source version"] = version

    # Create protein1 dataframe.
    protein1 = stringdbf[
        [
            "protein1",
            "protein1 id",
            "subject",
            "provided_by",
            "category",
        ]
    ]
    protein1["source"] = "STRING"  # source is STRING database
    protein1["source version"] = version  # source version
    
    protein1["id"] = protein1["subject"]  # id is the subject
    protein1["name"] = protein1["protein1 id"].map(namemapping)  # name is the mapped name
    protein1["xref"] = "ENSEMBL:" + protein1["protein1"].str.split(".").str[-1]  # xref is ENSEMBL:ensembl id
    protein1 = protein1[  # select the columns needed
        ["id", "name", "provided_by", "category", "xref", "source", "source version"]
    ]
    protein2 = stringdbf[
        [
            "protein2",
            "protein2 id",
            "object",
            "provided_by",
            "category"
        ],
    ]
    protein2["source"] = "STRING"  # source is STRING database
    protein2["source version"] = version  # source version

    protein2["id"] = protein2["object"]  # id is the object
    protein2["name"] = protein2["protein2 id"].map(namemapping)  # name is the mapped name
    protein2["xref"] = "ENSEMBL:" + protein2["protein2"].str.split(".").str[-1]  # xref is ENSEMBL:ensembl id
    protein2 = protein2[
        ["id", "name", "provided_by", "category", "xref", "source", "source version"]
    ]

    # Concatenate protein1 and protein2 to create the nodes dataframe and remove duplicates.
    nodes = pd.concat([protein1, protein2]).drop_duplicates()

    # Create the edges dataframe.
    edges = stringdbf[
        [
            "subject",
            "object",
            "knowledge_source",
            "predicate",
            "has_confidence_level",
        ]
    ].drop_duplicates()
    edges["source"] = "STRING"  # source is STRING database
    edges["source version"] = version  # source version
    edges["id"] = edges["subject"].apply(lambda x: uuid.uuid4())  # create a uuid for each edge

    # Save the nodes and edges to TSV files
    logging.info(f"Saving nodes to: {args.output[0]}")
    nodes.to_csv(f"{args.output[0]}", sep="\t", index=False)
    edges.to_csv(f"{args.output[1]}", sep="\t", index=False)


def get_parser():
    """
    Creates and configures an argument parser for the script.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="stringdb_to_kgx.py",
        description="Convert a STRING file to CSVs with nodes and edges.",
    )
    parser.add_argument("-i", "--input", help="Input STRING file") # input file
    parser.add_argument("-p", "--proteins", help="Input UniProt proteins file") # input file
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default=["string_nodes.tsv", "string_edges.tsv"],
        help="""
            Output prefixes for nodes and edges. 
            Default: string_nodes.tsv string_edges.tsv
            """,
    )
    return parser


if __name__ == "__main__":
    main()
