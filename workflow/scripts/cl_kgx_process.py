import argparse
import pandas as pd


def get_parser():
    parser = argparse.ArgumentParser(
        prog="cl_kgx_process.py",
        description="cl_kgx_process: convert protein ids from cl kgx files.",
    )
    parser.add_argument("-i", "--input", nargs="+", help="Input files")
    parser.add_argument("-m", "--mapping", help="Input files")
    parser.add_argument(
        "-o", "--output", nargs="+", default="cl", help="Output prefix. Default: out"
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    clnodes = pd.read_csv(args.input[0], sep="\t", low_memory=False)
    cledges = pd.read_csv(args.input[1], sep="\t", low_memory=False)
    clmapping = pd.read_csv(args.mapping, sep="\t", header=None, low_memory=False)

    clmapping.columns = ["ID", "xref", "Relation"]
    clmapping = (
        clmapping[clmapping["xref"].str.contains("UniProt")][["ID", "xref"]]
        .drop_duplicates()
        .set_index("ID")
    )

    clmapping = clmapping[~clmapping.index.duplicated(keep="first")].iloc[:, 0]

    # Transform nodes
    clnodes["Uniprot ID"] = (
        "UNIPROTKB:" + clnodes["id"].map(clmapping).str.split(":").str[-1]
    )
    cledges["Object Uniprot ID"] = (
        "UNIPROTKB:" + cledges["object"].map(clmapping).str.split(":").str[-1]
    )
    cledges["Subject Uniprot ID"] = (
        "UNIPROTKB:" + cledges["subject"].map(clmapping).str.split(":").str[-1]
    )

    clnodes["id"] = clnodes[["Uniprot ID", "id"]].bfill(axis=1).iloc[:, 0]
    cledges["object"] = (
        cledges[["Object Uniprot ID", "object"]].bfill(axis=1).iloc[:, 0]
    )
    cledges["subject"] = (
        cledges[["Subject Uniprot ID", "subject"]].bfill(axis=1).iloc[:, 0]
    )

    clnodes[["id", "category", "name", "provided_by"]].drop_duplicates().to_csv(
        f"{args.output[0]}", sep="\t", index=False
    )
    cledges[
        ["id", "subject", "predicate", "object", "relation", "knowledge_source"]
    ].to_csv(f"{args.output[1]}", sep="\t", index=False)


if __name__ == "__main__":
    main()
