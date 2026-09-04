import argparse
import pandas as pd
import uuid
# Function to read a TSV file into a pandas DataFrame.
# The main purpose of this function is to abstract the reading of the input files.
# The input is the filename.
# The output is a pandas DataFrame with the information of the input.
def read_files(fname):
    """Reads a tab-separated file into a pandas DataFrame.

    Args:
        fname (str): The path to the input file.

    Returns:
        pd.DataFrame: The DataFrame containing the file's data.
    """
    df = pd.read_csv(fname, sep="\t", low_memory=False)
    return df


def get_version(fname):
    with open(fname) as f:
        for line in f:
            if "version" in line:
                version = line.split("version ")[1].split(").")[0]
    return version

# Function to set up and return an argument parser.
# This function is used to define the arguments that the script can receive
# The input is None.
# The output is the argument parser.
# The arguments are:
# -i or --input: Input files.
# -v or --version: Input version file.
# -o or --output: Output prefix.
# The default output prefix is: out
def get_parser():
    parser = argparse.ArgumentParser(
        prog="disgenet_to_kgx.py",
        description=(
            "disgenet_to_csv: convert an disgenet file to CSVs with nodes and edges."
        ),
    )
    parser.add_argument("-i", "--input", nargs="+", help="Input files")
    parser.add_argument("-v", "--version", help="Input version file")
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default="disgenet",
        help="Output prefix. Default: out",
    )
    return parser


def main():
    # Initialize the parser and parse the arguments.
    parser = get_parser()
    args = parser.parse_args()
    # Read the input files into pandas DataFrames.
    # The first input file (args.input[0]) is the main DisGeNET data.
    disgenet = read_files(args.input[0])
    # The second input file (args.input[1]) is the mapping file for DisGeNET diseases.
    disgenet_mapping = read_files(args.input[1])
    # The third input file (args.input[2]) is the mapping between entrez gene id and ensembl gene id.
    entrez_to_ensembl = (
        read_files(args.input[2]).drop_duplicates().set_index("Entrez Gene ID")
    )

    # Remove duplicate entries by keeping the first occurrence of each index (Entrez Gene ID)
    # and selects the first column.
    entrez_to_ensembl = entrez_to_ensembl[
        ~entrez_to_ensembl.index.duplicated(keep="first")
    ].iloc[:, 0]

    # Transform the node.
    # Filter the mapping to keep only those with 'HPO' or 'MONDO' vocabulary.
    disgenet_mapping = disgenet_mapping[
        disgenet_mapping["vocabulary"].isin(["HPO", "MONDO"])
    ]
    # Concatenate vocabulary and code, replacing 'HPO:' with an empty string.
    disgenet_mapping["code"] = (
        disgenet_mapping["vocabulary"] + ":" + disgenet_mapping["code"]
    ).str.replace("HPO:", "")
    # Select 'diseaseId' and 'code', drop duplicates, and set 'diseaseId' as index.
    disgenet_mapping = (
        disgenet_mapping[["diseaseId", "code"]].drop_duplicates().set_index("diseaseId")
    )
    # Remove duplicate indices, keeping the first occurrence, and select the first column.
    disgenet_mapping = disgenet_mapping[
        ~disgenet_mapping.index.duplicated(keep="first")
    ].iloc[:, 0]
    # Change the geneid type to string to be uniform
    disgenet["geneId"] = disgenet["geneId"].map(str)

    # The main steps of this algorithm are:
    # 1. Read the files
    # 2. Filter the information
    # 3. Map the information.
    # 4. Generate the edges and nodes.
    # 5. Save the information.

    # Map 'diseaseId' to 'code' in the main disgenet DataFrame and add prefix to geneId
    # And add constants
    disgenet["object"] = disgenet["diseaseId"].map(disgenet_mapping)
    disgenet["subject"] = "NCBIGene:" + disgenet["geneId"]
    disgenet["provided_by"] = "Disgenet"
    disgenet["source"] = "Disgenet"
    disgenet["source version"] = get_version(args.version)

    disgenet = disgenet.dropna(subset=["object", "subject"])
    # Add publication formatting function
    def format_pmids(p):
        if pd.notnull(p):
            s = str(p).strip()
            if s.replace(".", "").isdigit():
                val = int(float(s))
                if val > 0:
                    return f"PMID:{val}"
        return ""

    disgenet["publications"] = disgenet["pmid"].apply(format_pmids) if "pmid" in disgenet.columns else ""

    # Generate nodes
    phenotypes = (
        disgenet[disgenet.object.str.startswith("HP")][
            ["object", "diseaseName", "provided_by", "source", "source version"]
        ]
        .rename(columns={"object": "id", "diseaseName": "name"})
        .assign(category="biolink:PhenotypicFeature")
    )
    diseases = (
        disgenet[disgenet.object.str.startswith("MONDO")][
            ["object", "diseaseName", "provided_by", "source", "source version"]
        ]
        .rename(columns={"object": "id", "diseaseName": "name"})
        .assign(category="biolink:Disease")
    )
    genes = (
        disgenet[["subject", "geneSymbol", "provided_by", "source", "source version"]]
        .rename(columns={"subject": "id", "geneSymbol": "name"})
        .assign(category="biolink:Gene")
    )
    nodes = pd.concat([genes, phenotypes, diseases], ignore_index=True).drop_duplicates(subset=["id"])
    nodes[["id", "name", "category", "provided_by", "source", "source version"]].to_csv(
        f"{args.output[0]}", sep="\t", index=False, lineterminator="\n"
    )

    # Filter the information about the gene to phenotype
    gene_to_phenotype = disgenet[disgenet.object.str.startswith("HP")].copy()
    gene_to_phenotype["category"] = "biolink:GeneToPhenotypicFeatureAssociation"
    gene_to_phenotype["predicate"] = "biolink:associated_with"
    gene_to_phenotype["relation"] = "RO:0016001"
    gene_to_phenotype["knowledge_source"] = "Disgenet"

    # Filter the information about the gene to disease
    gene_to_disease = disgenet[disgenet.object.str.startswith("MONDO")].copy()
    gene_to_disease["category"] = "biolink:GeneToDiseaseAssociation"
    gene_to_disease["predicate"] = "biolink:associated_with"
    gene_to_disease["relation"] = "RO:0016001"
    gene_to_disease["knowledge_source"] = "Disgenet"

    edges = pd.concat([gene_to_phenotype, gene_to_disease], ignore_index=True)
    edge_group_cols = [
        "subject",
        "predicate",
        "object",
        "category",
        "relation",
        "knowledge_source",
        "source",
        "source version",
    ]
    edges = (
        edges.groupby(edge_group_cols)["publications"]
        .apply(lambda s: "|".join(sorted(set(x for x in s if x))[:50]))
        .reset_index()
    )
    edges["id"] = edges["subject"].apply(lambda x: uuid.uuid4())

    # Save the edges
    edges[
        [
            "id",
            "subject",
            "predicate",
            "object",
            "category",
            "relation",
            "publications",
            "knowledge_source",
            "source",
            "source version",
        ]
    ].to_csv(f"{args.output[1]}", sep="\t", index=False, lineterminator="\n")

# Check the file name
if __name__ == "__main__":
    main()
