import argparse
import pandas as pd
import uuid

# Import necessary libraries: argparse for command-line argument parsing, pandas for data manipulation,
# and uuid for generating unique identifiers.

# Define a dictionary to map interaction classes to Biolink predicates.
# This dictionary defines the mapping between interaction classes (like "binding", "regulatory")
# and their corresponding Biolink predicates.
predicates = {
    # Define predicates for different interaction types. "binding" and "binding;regulatory" are mapped to "biolink:binds".
    "binding": "biolink:binds",
    "binding;regulatory": "biolink:binds",

    # Define predicates per class.
    "regulatory": "biolink:regulates",
    "expression correlation": "biolink:correlates",
    "coexpression": "biolink:coexpressed_with",
}

# Specifies the columns that represent genes in the input files.
GENES = ["Gene Id", "Gene Version", "Gene Name"]

# Define the expected columns for RNAcentral data.
RNACENTRALMAPPING = [
    "RNACentral ID",
    "DB",
    "Transcript ID",
    "Species",
    "RNA Type",
    "Gene ID"
]  # Defines the expected column names for the RNAcentral data.


# Function to add predicate mappings to the DataFrame based on the 'class' column
def add_predicates(df):
    # This function adds a 'predicate' column to the DataFrame based on the 'class' column and the 'predicates' dictionary.
    # Drop duplicate predicates for cleaner mapping
    predicatef = pd.Series(predicates).drop_duplicates()
    # Map the 'class' column to the 'predicate' column using the 'predicatef' mapping.
    df["predicate"] = df["class"].map(predicatef)
    # Return the modified DataFrame.
    return df


# Function to read RNAcentral data from multiple files and extract relevant information.
# This function can read the RNA mappings from either the transcript or the gene.
def read_rna(fnames, type):
    # Initialize an empty DataFrame to store the RNA mappings.
    rnamapping = pd.DataFrame()
    # Iterate through each file name in the 'fnames' list.
    for f in fnames:
        # Read the file into a DataFrame, assuming tab-separated values.
        df = pd.read_csv(f, sep="\t", low_memory=False, header=None)  # Read RNA data from file.
        # Set the column names based on the 'RNACENTRALMAPPING' list.
        df.columns = RNACENTRALMAPPING
        # Concatenate the data from each file into the 'rnamapping' DataFrame.
        rnamapping = pd.concat([rnamapping, df])
    # Extract the base ID by splitting at the first dot and take the first part.
    rnamapping["ID"] = rnamapping[type].str.split(".").str[0]
    # Keep only the needed columns
    rnamapping = rnamapping[["ID", "RNACentral ID"]].drop_duplicates().set_index("ID")
    #Remove duplicated indices
    rnamapping = rnamapping[~rnamapping.index.duplicated(keep="first")].iloc[:, 0]
    # Return the mapping as a pandas serie
    return rnamapping


# Function to read gene data from a file, format it, and return a Series
def read_genes(fname):
    # Read the gene data from the specified file, assuming semicolon-separated values.
    df = pd.read_csv(fname, sep=";", low_memory=False, header=None)  # Read gene data from file.
    # Keep only the first three columns.
    df = df.iloc[:, :3]
    # Set the column names according to the GENES list.
    df.columns = GENES
    # Filter rows that contain 'gene_name' in the 'Gene Name' column. Only keep genes.
    df = df[df["Gene Name"].str.contains("gene_name")]  # Filter rows for gene names.
    # Format the 'Gene Id' by adding the ENSEMBL: prefix and cleaning the ID.
    df["Gene Id"] = "ENSEMBL:" + df["Gene Id"].str.split(" ").str[-1].str.replace('"', "")
    # Clean the gene name.
    df["Gene Name"] = df["Gene Name"].str.split(" ").str[-1].str.replace('"', "")
    # Keep only Gene ID and gene name.
    df = df[["Gene Id", "Gene Name"]].drop_duplicates().set_index("Gene Name")
    # Remove duplicates.
    df = df[~df.index.duplicated(keep="first")].iloc[:, 0]
    # Return a pandas Series.
    return df


# Function to read UniProt ID mapping data, filter it, and return a Series
def read_id_mapping_uniprot(fname):
    # Reads a file containing UniProt ID mappings and returns a pandas series of mappings.
    df = pd.read_csv(fname, sep="\t", header=None, low_memory=False)  # Read UniProt ID mappings from file.
    #Set the columns names
    df.columns = ["ID", "Database", "Database ID"]
    # Filter the database ID to only keep the uniprot IDs
    df = df[df["Database"] == "UniProtKB-ID"]
    # Clean the Database ID to only keep the uniprot ID
    df["Database ID"] = df["Database ID"].str.split("_").str[0]
    # Keep the needed columns
    df = df[["ID", "Database ID"]].drop_duplicates().set_index("ID")
    #Remove duplicates
    df = df[~df.index.duplicated(keep="first")].iloc[:, 0]
    #Return the mapping
    return df


# Function to set up command-line argument parsing
def get_parser():
    # Create an argument parser with a description of the script.
    parser = argparse.ArgumentParser(
        prog="npinter_to_kgx.py",
        description="npinter_to_kgx: convert an npinter file to CSVs with nodes and edges.",
    )
    parser.add_argument("-i", "--input", help="Input files")
    parser.add_argument("-p", "--proteins", help="Input files")
    parser.add_argument("-g", "--genes", help="Input files")
    parser.add_argument("-r", "--rna", nargs="+", help="Input files")
    # Define the output file name.
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default="npinter",
        help="Output prefix. Default: out",
    )
    return parser


# Main function to orchestrate the data processing
def main():
    # Get the parser.
    parser = get_parser()
    # Parse the arguments.
    args = parser.parse_args()

    # Read input files.
    # Read the NPInter data and add the predicates to it.
    npinterf = pd.read_csv(args.input, sep="\t", low_memory=False)
    npinterf = add_predicates(npinterf)
    # Read mapping files.
    # Read the uniprot, ensembl and rnacentral mappings.
    uniprotf = read_id_mapping_uniprot(args.proteins)
    ensemblf = read_genes(args.genes)
    rnacentraltf = read_rna(args.rna, "Transcript ID")
    rnacentralgf = read_rna(args.rna, "Gene ID")

    # Extract the version from the input filename.
    version = args.input.split("/")[-1]
    # Clean the version string.
    version = version.split(".")[0].split("_")[1]

    # Map the RNA IDs.
    # Get the rnacentral id
    npinterf["RNACentral Transcript"] = npinterf["ncID"].map(rnacentraltf)
    npinterf["RNACentral Gene"] = npinterf["ncID"].map(rnacentralgf)
    npinterf["subject"] = (
        npinterf[["RNACentral Transcript", "RNACentral Gene"]].bfill(axis=1).iloc[:, 0]
    )
    npinterf = npinterf.dropna(subset=["subject"])
    npinterf["subject"] = "RNACENTRAL:" + npinterf["subject"]
    npinterf["provided_by"] = "NPInter"
    npinterf["knowledge_source"] = "NPInter"
    npinterf["source"] = "NPInter"
    npinterf["source version"] = version

    # Process RNA-Protein interactions.
    npinterproteins = npinterf[npinterf["level"].isin(["RNA-Protein"])]
    npinterproteins["Uniprot Name"] = npinterproteins["tarID"].map(uniprotf)
    npinterproteins = npinterproteins.dropna(subset=["Uniprot Name"])
    npinterproteins["object"] = "UNIPROTKB:" + npinterproteins["tarID"]

    # Generate node files for Proteins
    # Create a dataframe with the needed information for the proteins nodes
    proteins = npinterproteins[
        ["object", "provided_by", "Uniprot Name", "source", "source version"]
    ]
    # Set id name and category
    proteins["id"] = proteins["object"]
    proteins["name"] = proteins["Uniprot Name"]
    proteins["category"] = "biolink:Protein"
    # Clean the columns
    proteins = proteins[
        ["id", "name", "provided_by", "category", "source", "source version"]
    ].drop_duplicates()

    # Process RNA-RNA interactions.
    npinterrna = npinterf[npinterf["level"].isin(["RNA-RNA"])]
    npinterrna["RNACentral Transcript"] = npinterrna["tarID"].map(rnacentraltf)
    # get the rnacentral id for genes
    npinterrna["RNACentral Gene"] = npinterrna["tarID"].map(rnacentralgf)
    #Merge the 2 columns to get the rnacentral id
    npinterrna["object"] = (
        npinterrna[["RNACentral Transcript", "RNACentral Gene"]] # Fill empty values
        .bfill(axis=1)
        .iloc[:, 0]
    )
    npinterrna = npinterrna.dropna(subset=["object"])
    npinterrna["object"] = "RNACENTRAL:" + npinterrna["object"]

    # Generate node files for the other RNA
    rnaobj = npinterrna[
        [
            # List of the needed columns
            "object",
            "provided_by",
            "tarName",
            "tarType",
            "tarID",
            "source",
            "source version",
        ]
    ] # Define id name node property xref and category
    rnaobj["id"] = rnaobj["object"]
    rnaobj["name"] = rnaobj["tarName"]
    rnaobj["category"] = "biolink:RNAProduct"
    rnaobj["node_property"] = rnaobj["tarType"]
    # The xref is the ID
    rnaobj["xref"] = rnaobj["tarID"]
    # Clean the columns
    rnaobj = rnaobj[
        [
            "id",
            "name",
            "provided_by",
            "category",
            "xref",
            "node_property",
            "source",
            "source version",
        ]
    ].drop_duplicates()

    # Process RNA-DNA interactions.
    npintergenes = npinterf[npinterf["level"].isin(["RNA-DNA"])]
    npintergenes["Ensembl ID"] = npintergenes["tarName"].map(ensemblf)
    npintergenes = npintergenes.dropna(subset=["Ensembl ID"])
    npintergenes["object"] = npintergenes["Ensembl ID"]

    # Generate node files for genes.
    # Get the needed information.
    genes = npintergenes[
        ["object", "provided_by", "tarName", "source", "source version"]
    ]
    genes["id"] = genes["object"]
    genes["name"] = genes["tarName"]
    genes["category"] = "biolink:Gene"
    genes = genes[
        ["id", "name", "provided_by", "category", "source", "source version"]
    ].drop_duplicates()

    # Generate node files for RNA.
    rna = npinterf[
        [
            #list of needed columns
            "subject",
            "ncID",
            "provided_by",
            "ncType",
            "ncName",
            "source",
            "source version",
        ]
    ]
    # define id name, xref, node_property and category
    rna["id"] = rna["subject"]
    rna["name"] = rna["ncName"]
    rna["category"] = "biolink:RNAProduct"
    rna["xref"] = rna["ncID"]
    rna["node_property"] = rna["ncType"]
    # clean the dataframe columns

    rna = rna[
        [
            "id",
            "name",
            "provided_by",
            "category",
            "xref",
            "node_property",
            "source",
            "source version",
        ]
    ].drop_duplicates()

    # Concatenate all nodes together.
    nodes = pd.concat([proteins, genes, rna, rnaobj]).drop_duplicates()
    # Create the edges dataframe.
    edges = pd.concat(  # Concatenate the edges
        [
            # get needed columns
            npintergenes[
                # list of needed columns
                [
                    "subject",
                    "object",
                    "knowledge_source",
                    "predicate",
                    "source",
                    "source version",
                ]
            ],
             # get needed columns
            npinterrna[
                [
                    "subject",
                    "object",
                    "knowledge_source",
                    "predicate",
                    "source",
                    "source version",
                ]
            ],
            # get needed columns
            npinterproteins[
                [
                    "subject",
                    "object",
                    "knowledge_source",
                    "predicate",
                    "source",
                    "source version",
                ]
            ],
        ]
    )
    # Create a unique id for each edge.
    edges["id"] = edges["subject"].apply(lambda x: uuid.uuid4())

    # Save to the defined files.
    nodes.to_csv(f"{args.output[0]}", sep="\t", index=False)
    # Save to the defined files.
    edges.to_csv(f"{args.output[1]}", sep="\t", index=False)


if __name__ == "__main__":
    main()
