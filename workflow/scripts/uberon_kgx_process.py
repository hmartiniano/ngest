import pandas as pd
import argparse
import requests

release = "https://api.github.com/repos/obophenotype/uberon/releases/latest"


def get_parser():
    parser = argparse.ArgumentParser(
        prog="uberon_kgx_process.py",
        description=("uberon_kgx_process: get uberon version."),
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

    parser = get_parser()
    args = parser.parse_args()
    uberonnodes = pd.read_csv(args.input[0], sep="\t", low_memory=False)
    uberonedges = pd.read_csv(args.input[1], sep="\t", low_memory=False)

    response = requests.get(release)
    version = response.json()["name"]

    uberonnodes["source"] = "Uberon"
    uberonnodes["source version"] = version

    uberonedges["source"] = "Uberon"
    uberonedges["source version"] = version

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


if __name__ == "__main__":
    main()
