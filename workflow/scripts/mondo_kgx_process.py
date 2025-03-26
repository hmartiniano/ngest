import pandas as pd
import argparse
import requests
# Define the URL for the latest release of the MONDO ontology from the Monarch Initiative GitHub repository.
release = "https://api.github.com/repos/monarch-initiative/mondo/releases/latest"


def get_parser():
    """
    Creates and returns an argument parser for the script.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="mondo_kgx_process.py",
        description=("mondo_kgx_process: get mondo version."),
    )
    # add input file arguments
    parser.add_argument("-i", "--input", nargs="+", help="Input files")
    # add output file prefix arguments
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default="out",
        help="Output prefix. Default: out",
    )
    return parser


def main():

    # Get command-line arguments
    parser = get_parser()
    args = parser.parse_args()
    # Read the input files into pandas DataFrames
    mondonodes = pd.read_csv(args.input[0], sep="\t", low_memory=False)
    mondoedges = pd.read_csv(args.input[1], sep="\t", low_memory=False)

    # Get the latest MONDO release version from GitHub API
    response = requests.get(release)
    version = response.json()["name"]

    # Add source and source version columns to the DataFrames
    mondonodes["source"] = "MONDO"
    mondonodes["source version"] = version

    mondoedges["source"] = "MONDO"
    mondoedges["source version"] = version

    # output the dataframes to tsv format 
    # select the columns from the dataframes and drop duplicates if any
    mondonodes[
        [
            "id",
            "category",
            "name",
            "provided_by",
            "description",
            "xref",
            "source",
            "source version",
        ]
    ].drop_duplicates().to_csv(f"{args.output[0]}", sep="\t", index=False)
    mondoedges[
        [
            "id",
            "subject",
            "predicate",
            "object",
            "relation",
            "knowledge_source",
            "source",
            "source version",
        ]
    ].to_csv(f"{args.output[1]}", sep="\t", index=False)
#entry point

if __name__ == "__main__":
    main()
