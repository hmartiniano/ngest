# Import necessary libraries
import pandas as pd
import argparse
import requests

# Define the URL for the latest release of the Uberon ontology on GitHub
release = "https://api.github.com/repos/obophenotype/uberon/releases/latest"


def get_parser():
    """
    Create and configure the argument parser for the script.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="uberon_kgx_process.py",
        description=("uberon_kgx_process: get uberon version."),
    )
    # Add an argument for input files
    parser.add_argument("-i", "--input", nargs="+", help="Input files")
    # Add an argument for the output prefix, with a default value
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default="out",
        help="Output prefix. Default: out",
    )
    return parser


def main():
    """
    Main function to process Uberon data, extract version information, and save the data.
    """
    # Get the argument parser
    parser = get_parser()
    # Parse the arguments from the command line
    args = parser.parse_args()
    # Read the Uberon nodes data from the first input file
    uberonnodes = pd.read_csv(args.input[0], sep="\t", low_memory=False)
    # Read the Uberon edges data from the second input file
    uberonedges = pd.read_csv(args.input[1], sep="\t", low_memory=False)

    # Get the latest release information from GitHub API
    response = requests.get(release)
    # Extract the version name from the JSON response
    version = response.json()["name"]

    # Add a "source" column to the nodes dataframe and fill it with "Uberon"
    uberonnodes["source"] = "Uberon"
    # Add a "source version" column to the nodes dataframe and fill it with the version
    uberonnodes["source version"] = version

    # Add a "source" column to the edges dataframe and fill it with "Uberon"
    uberonedges["source"] = "Uberon"
    # Add a "source version" column to the edges dataframe and fill it with the version
    uberonedges["source version"] = version

    # Select specific columns, drop duplicates, and save the nodes data to a tab-separated file
    uberonnodes[
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
    # Select specific columns and save the edges data to a tab-separated file
    uberonedges[
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


# Check if the script is run as the main program
if __name__ == "__main__":
    main()
