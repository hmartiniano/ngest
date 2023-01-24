import pandas as pd
import argparse
import requests

release = "https://api.github.com/repos/monarch-initiative/mondo/releases/latest"
def get_parser():
    parser = argparse.ArgumentParser(
        prog="mondo_kgx_process.py",
        description=(
            "mondo_kgx_process: get mondo version."
        ),
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
    mondonodes = pd.read_csv(args.input[0], sep="\t", low_memory=False)
    mondoedges = pd.read_csv(args.input[1], sep="\t", low_memory=False)

    response = requests.get(
        release
    )
    version = response.json()["name"]

    mondonodes["source"] = "MONDO"
    mondonodes["source version"] = version

    mondoedges["source"] = "MONDO"
    mondoedges["source version"] = version

    mondonodes[["id", "category", "name", "provided_by", "description", "xref", "source","source version"]].drop_duplicates().to_csv(
        f"{args.output[0]}", sep="\t", index=False
    )
    mondoedges[
        ["id", "subject", "predicate", "object", "relation", "knowledge_source", "source", "source version"]
    ].to_csv(f"{args.output[1]}", sep="\t", index=False)

if __name__ == "__main__":
    main()