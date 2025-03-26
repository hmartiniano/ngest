import pandas as pd
import argparse
import requests
"""
This script processes HPO (Human Phenotype Ontology) data and prepares it for KGX (Knowledge Graph Exchange) format.
It retrieves the latest HPO release version from GitHub, adds source and version information to HPO nodes and edges,
and outputs the processed data to TSV files.
"""
# URL for the latest HPO release on GitHub
release = (
    "https://api.github.com/repos/obophenotype/human-phenotype-ontology/releases/latest"
)


def get_parser():
    # Create and configure an argument parser for command-line inputs
    parser = argparse.ArgumentParser(
        prog="hpo_kgx_process.py",
        description=("hpo_kgx_process: get hpo version."),
    )
    parser.add_argument("-i", "--input", nargs="+", help="Input files")
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default="go",
        help="Output prefix. Default: out",
    )
    return parser


def main():
    # Parse command-line arguments
    parser = get_parser()
    args = parser.parse_args()
    # Read HPO nodes and edges from input files
    hponodes = pd.read_csv(args.input[0], sep="\t", low_memory=False)
    hpoedges = pd.read_csv(args.input[1], sep="\t", low_memory=False)

    # Retrieve the latest HPO release version from GitHub API
    response = requests.get(release)
    version = response.json()["name"]

    # Add source information and version to HPO nodes
    hponodes["source"] = "HPO"
    hponodes["source version"] = version

    # Add source information and version to HPO edges
    hpoedges["source"] = "HPO"
    hpoedges["source version"] = version

    hponodes[
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
        # drop duplicates
    ].drop_duplicates().to_csv(f"{args.output[0]}", sep="\t", index=False)
    hpoedges[
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
# Entry point of the script

if __name__ == "__main__":
    main()
