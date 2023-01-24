import pandas as pd
import argparse
import json

def get_parser():
    parser = argparse.ArgumentParser(
        prog="go_kgx_process.py",
        description=(
            "go_kgx_process: get go version."
        ),
    )
    parser.add_argument("-i", "--input", nargs="+", help="Input files")
    parser.add_argument("-v", "--version", help="Input version file")
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
    gonodes = pd.read_csv(args.input[0], sep="\t", low_memory=False)
    goedges = pd.read_csv(args.input[1], sep="\t", low_memory=False)

    with open(args.version, "r") as f:
        version = json.load(f)["date"]

    gonodes["source"] = "GO"
    gonodes["source version"] = version

    goedges["source"] = "GO"
    goedges["source version"] = version

    gonodes[["id", "category", "name", "provided_by", "description", "xref", "source", "source version"]].drop_duplicates().to_csv(
        f"{args.output[0]}", sep="\t", index=False
    )
    goedges[
        ["id", "subject", "predicate", "object", "relation", "knowledge_source", "source", "source version"]
    ].to_csv(f"{args.output[1]}", sep="\t", index=False)

if __name__ == "__main__":
    main()