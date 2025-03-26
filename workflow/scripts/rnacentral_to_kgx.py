import uuid
import argparse
import pandas as pd
# Define the expected column names for the RNACentral mapping file.
RNACENTRALMAPPING = [
    "RNACentral ID",
    "DB",
    "Transcript ID",
    "Species",
    "RNA Type",
    "Gene ID",
]  
# Define the expected column names for the RNACentral file.
RNACENTRAL = ["DB", "RNACentral ID", "Name", "Type"]
# Define the expected column names for the genes file.
GENES = ["Gene Id", "Gene Version", "Gene Name"]


def read_file(fname, columns):
    """
    Reads a tab-separated file into a pandas DataFrame with specified columns.
    
    Args:
        fname (str): The path to the file.
        columns (list): A list of column names.
    
    Returns:
        pandas.DataFrame: The DataFrame containing the file data.
    """
    df = pd.read_csv(fname, sep="\t", header=None, comment="!", low_memory=False)
    df.columns = columns
    return df


def get_version(fname):
    """Extracts the version number from the second line of a file."""
    with open(fname) as f:
        version = f.readlines()[1].split("\n")[0]
    return version

def read_genes(fname):
    df = pd.read_csv(fname, sep=";", low_memory=False, header=None)
    df = df.iloc[:, :3]
    df.columns = GENES
    df = df[df["Gene Name"].str.contains("gene_name")]
    df["Gene Id"] = "ENSEMBL:" + df["Gene Id"].str.split(" ").str[-1].str.replace(
        '"', ""
    )
    df["Gene Name"] = df["Gene Name"].str.split(" ").str[-1].str.replace('"', "")
    df = df[["Gene Id", "Gene Name"]].drop_duplicates().set_index("Gene Id")
    df = df[~df.index.duplicated(keep="first")].iloc[:, 0]
    return df

"""
    Configures the command-line argument parser for the script.
    
    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    
    
def get_parser():
    parser = argparse.ArgumentParser(
        prog="rnacentral_to_kgx.py",
        description=(
            "rnacentral_to_kgx: convert an rnacentral file to CSVs with nodes and"
            " edges."
        ),
    )
    parser.add_argument("-i", "--input", help="Input files")
    parser.add_argument("-m", "--mapping", help="Input files")
    parser.add_argument("-g", "--genes", help="Input files")
    parser.add_argument("-v", "--version", help="Version file")
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default="ensembl",
        help="Output prefix. Default: out",
    )
    return parser


def main():    
    parser = get_parser()
    args = parser.parse_args()

    # get the file version
    version = get_version(args.version)
    
    # create the rnacentral mapping
    rnacentralmapping = read_file(args.mapping, RNACENTRALMAPPING)
    rnacentralmapping["Gene ID"] = rnacentralmapping["Gene ID"].str.split(".").str[0]
    
    # map the gene id to the rnacentral id
    rnacentralgenemapping = (
        rnacentralmapping[["RNACentral ID", "Gene ID"]]
        .drop_duplicates()
        .set_index("RNACentral ID")
    )
    rnacentralgenemapping = rnacentralgenemapping[
        ~rnacentralgenemapping.index.duplicated(keep="first")
    ].iloc[:, 0]    
    # map the transcript id to the rnacentral id

    rnacentralrnamapping = (
        rnacentralmapping[["RNACentral ID", "Transcript ID"]]
        .drop_duplicates()
        .set_index("RNACentral ID")
    )
    rnacentralrnamapping = rnacentralrnamapping[
        ~rnacentralrnamapping.index.duplicated(keep="first")
    ].iloc[:, 0]
    # extract the ensembl gene names
    genenames = read_genes(args.genes)
    
    # process the rnacentral file
    rnacentral = read_file(args.input, RNACENTRAL)
    rnacentral["RNACentral ID"] = (
        rnacentralmapping["RNACentral ID"].str.split("_").str[0]
    )
    rnacentral["Ensembl Gene ID"] = rnacentral["RNACentral ID"].map(
        rnacentralgenemapping
    )
    rnacentral["Ensembl Transcript ID"] = rnacentral["RNACentral ID"].map(
        rnacentralrnamapping
    )
    
    # populate metadata
    rnacentral["provided_by"] = rnacentral["DB"].str.upper()
    rnacentral["knowledge_source"] = rnacentral["DB"].str.upper()

    rnacentral["subject"] = "ENSEMBL:" + rnacentral["Ensembl Gene ID"]
    rnacentral["object"] = "RNACENTRAL:" + rnacentral["RNACentral ID"]
    rnacentral["predicate"] = "biolink:has_gene_product"
    rnacentral["relation"] = "RO:0002205"
    rnacentral["source"] = "RNACentral"
    rnacentral["source version"] = version
    rnacentral = rnacentral.dropna(subset=["object", "subject"])

    #create edges df
    edges = rnacentral[ 
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
    edges["id"] = rnacentral["subject"].apply(lambda x: uuid.uuid4())

    rna = rnacentral[ #create rna df
        [
            "object",
            "Type",
            "provided_by",
            "Name",
            "Ensembl Transcript ID",
            "source",
            "source version",
        ]
    ]
    rna["id"] = rna["object"]
    rna["category"] = "biolink:RNAProduct"
    rna["name"] = rna["Name"]
    rna["xref"] = "ENSEMBL:" + rna["Ensembl Transcript ID"]
    rna["node_property"] = rna["Type"]
    rna = rna[
        [
            "id",
            "category",
            "name",
            "xref",
            "provided_by",
            "node_property",
            "source",
            "source version",
        ]
    ]
    
    genes = rnacentral[["subject", "provided_by", "source", "source version"]] #create gene df
    genes["id"] = genes["subject"]
    genes["name"] = genes["subject"].map(genenames)
    genes["category"] = "biolink:Gene"
    genes = genes[["id", "category", "name", "provided_by", "source", "source version"]]

    nodes = pd.concat([genes, rna]).drop_duplicates()

    nodes[
        [
            "id",
            "name",
            "category",
            "provided_by",
            "xref",
            "node_property",
            "source",
            "source version",
        ]
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


#Entry point
if __name__ == "__main__":
    main()
