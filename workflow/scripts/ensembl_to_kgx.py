import re
import uuid
import argparse
import pandas as pd

# Define the expected columns for gene data
GENES = ["Gene Id", "Gene Version", "Gene Name"]


def read_id_mapping_uniprot(fname):
    """
    Reads a UniProt ID mapping file and returns a Series mapping UniProt IDs to their database IDs.
    Args:
        fname (str): The path to the UniProt ID mapping file.
    Returns:
        pd.Series: A Series with UniProt IDs as index and database IDs as values.
    """
    df = pd.read_csv(fname, sep="\t", header=None, low_memory=False)
    df.columns = ["ID", "Database", "Database ID"]
    df = df[df["Database"] == "UniProtKB-ID"]
    df["Database ID"] = df["Database ID"].str.split("_").str[0]
    df = df[["ID", "Database ID"]].drop_duplicates().set_index("ID")
    df = df[~df.index.duplicated(keep="first")].iloc[:, 0]  # Remove duplicated indexes
    return df


def read_genes(fname):
    gene_map = {}
    with open(fname, "r") as f:
        for line in f:
            m_id = re.search(r'gene_id\s+"([^"]+)"', line)
            m_name = re.search(r'gene_name\s+"([^"]+)"', line)
            if m_id and m_name:
                gene_map["ENSEMBL:" + m_id.group(1)] = m_name.group(1)
            elif m_id:
                gid = "ENSEMBL:" + m_id.group(1)
                if gid not in gene_map:
                    gene_map[gid] = m_id.group(1)
    return pd.Series(gene_map)


def get_parser():
    """Defines the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="ensembl_to_kgx.py",
        description=(
            "ensembl_to_csv: convert an ensembl file to CSVs with nodes and edges."
        ),
    )
    parser.add_argument("-i", "--input", help="Input files")
    parser.add_argument("-u", "--uniprot", help="Input files")
    parser.add_argument("-g", "--genes", help="Input files")
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default="ensembl",
        help="Output prefix. Default: out",
    )
    return parser


def main():
    """Main function to process Ensembl, UniProt, and gene data and generate KGX files."""
    parser = get_parser()
    args = parser.parse_args()  # Parse command-line arguments
    uniprotf = read_id_mapping_uniprot(args.uniprot)  # Read and process UniProt data
    ensemblf = pd.read_csv(
        args.input, sep="\t", comment="!", low_memory=False
    )  # Read Ensembl data
    genesf = read_genes(args.genes)  # Read and process gene data

    ensemblf["protein name"] = ensemblf["xref"].map(
        uniprotf
    )  # Map UniProt IDs to protein names
    ensemblf["provided_by"] = "ENSEMBL"
    ensemblf["knowledge_source"] = "ENSEMBL"
    ensemblf["xref"] = ensemblf["xref"].str.split("-").str[0]  # clean xref names
    ensemblf["protein name"] = ensemblf["xref"].map(
        uniprotf
    )  # Map UniProt IDs to protein names
    ensemblf["source"] = "ENSEMBL"
    version = args.input.split(".")
    ensemblf["source version"] = version[3] + " " + version[4] # take the version from the name

    gene_to_protein = ensemblf.dropna(subset=["xref"])  # Drop rows without xref
    gene_to_protein["subject"] = (
        "ENSEMBL:" + gene_to_protein["gene_stable_id"]
    )
    gene_to_protein["object"] = "UNIPROTKB:" + gene_to_protein["xref"]
    gene_to_protein["predicate"] = "biolink:has_gene_product"
    gene_to_protein["relation"] = "RO:0002205"
    gene_to_protein = gene_to_protein[
        [
            "subject",
            "predicate",
            "object",
            "relation",
            "knowledge_source",
            "source",
            "source version",
        ]
    ].drop_duplicates()
    gene_to_protein["id"] = gene_to_protein["subject"].apply(
        lambda x: uuid.uuid4()
    )  # Assign unique IDs

    protein = ensemblf.dropna(subset=["xref"])  # Drop rows without xref

    protein["id"] = "UNIPROTKB:" + protein["xref"]
    protein["category"] = "biolink:Protein"
    protein["name"] = protein["protein name"]
    protein["xref"] = "ENSEMBL:" + ensemblf["protein_stable_id"]
    protein = protein[
        [
            "id",
            "category",
            "name",
            "xref",
            "provided_by",
            "source",
            "source version",
        ]
    ]  # Select specific columns

    edges = gene_to_protein  # Define edges DataFrame

    genes = ensemblf  # Create a new DataFrame for genes
    genes["id"] = "ENSEMBL:" + ensemblf["gene_stable_id"]  # Assign gene IDs
    genes["category"] = "biolink:Gene"  # Assign category
    genes["name"] = genes["id"].map(genesf)  # Map gene names
    genes = genes[
        ["id", "category", "name", "provided_by", "source", "source version"]
    ]  # Select specific columns

    nodes = pd.concat([genes, protein]).drop_duplicates()  # Concatenate gene and protein

    nodes[
        ["id", "name", "category", "provided_by", "xref", "source", "source version"]  # select columns
    ].to_csv(f"{args.output [0]}", sep="\t", index=False)
    edges[
        [
            "object",
            "subject",
            "id",
            "predicate",
            "knowledge_source",
            "relation",
            "source",
            "source version",
        ]
    ].to_csv(f"{args.output[1]}", sep="\t", index=False)
    # output node and edge file in KGX

if __name__ == "__main__":  # Execute main function when the script is run
    main()  # execute main function
