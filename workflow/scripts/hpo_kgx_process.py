import pandas as pd
import argparse
import requests

release = "https://api.github.com/repos/obophenotype/human-phenotype-ontology/releases/latest"
def get_parser():
    parser = argparse.ArgumentParser(
        prog="hpo_kgx_process.py",
        description=(
            "hpo_kgx_process: get hpo version."
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
    hponodes = pd.read_csv(args.input[0], sep="\t", low_memory=False)
    hpoedges = pd.read_csv(args.input[1], sep="\t", low_memory=False)

    response = requests.get(
        release
    )
    version = response.json()["name"]

    hponodes["source"] = "HPO"
    hponodes["source version"] = version

    hpoedges["source"] = "HPO"
    hpoedges["source version"] = version

    hponodes[["id", "category", "name", "provided_by", "description", "xref", "source","source version"]].drop_duplicates().to_csv(
        f"{args.output[0]}", sep="\t", index=False
    )
    hpoedges[
        ["id", "subject", "predicate", "object", "relation", "knowledge_source", "source", "source version"]
    ].to_csv(f"{args.output[1]}", sep="\t", index=False)

if __name__ == "__main__":
    main()