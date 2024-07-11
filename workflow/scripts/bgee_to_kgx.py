import argparse
import pandas as pd
import uuid


def read_files(fname):
    """Reads a CSV file into a pandas DataFrame.

    Args:
        fname (str): The path to the CSV file.
    Returns:
        pandas.DataFrame: A pandas DataFrame containing the data from the CSV file.

    Raises:
        IOError: If the file cannot be read.
    """
    df = pd.read_csv(fname, sep="\t", low_memory=False)
    return df


def get_parser():
    parser = argparse.ArgumentParser(
        prog="bgee_to_kgx.py",
        description="bgee_to_csv: convert an bgee file to CSVs with nodes and edges.",
    )
    parser.add_argument("-i", "--input", help="Input files")
    parser.add_argument(
        "-o", "--output", nargs="+", default="bgee", help="Output prefix. Default: out"
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    bgee = read_files(args.input)

    # bgee = bgee[bgee["Expression"].isin(["present", "absent"])]

    bgee = bgee[bgee["Expression"].isin(["present"])]
    bgee["object"] = bgee["Anatomical entity ID"]
    bgee["subject"] = "ENSEMBL:" + bgee["Gene ID"]
    bgee["provided_by"] = "BGEE"
    bgee = bgee[~bgee["object"].str.contains("∩", na=False)]

    bgee["source"] = "BGEE"
    url = args.input.split("/")[-1]
    bgee["source version"] = url.split("_")[1] + "_" + url.split("_")[2]

    gene_to_ae = bgee
    gene_to_ae["category"] = "biolink:GeneToExpressionSiteAssociation"
    gene_to_ae["predicate"] = "biolink:expressed_in"
    gene_to_ae["relation"] = "RO:0002206"
    gene_to_ae["knowledge_source"] = "BGEE"

    #  to include negated field for absent relations
    #   gene_to_ae["negated"] = gene_to_ae.Expression.str.startswith("absent")

    gene_to_ae = gene_to_ae[
        [
            "subject",
            "predicate",
            "object",
            "category",
            "relation",
            "knowledge_source",
            "source",
            "source version",
        ]
    ].drop_duplicates()
    gene_to_ae["id"] = gene_to_ae["subject"].apply(lambda x: uuid.uuid4())
    gene_to_ae.to_csv(f"{args.output[1]}", sep="\t", index=False)

    ae = bgee[
        ["object", "Anatomical entity name", "provided_by", "source", "source version"]
    ]
    ae["id"] = ae["object"]
    ae["name"] = ae["Anatomical entity name"]
    ae.loc[ae["id"].str.contains("UBERON"), "category"] = "biolink:AnatomicalEntity"
    ae.loc[ae["id"].str.contains("CL"), "category"] = "biolink:Cell"

    genes = bgee[["subject", "provided_by", "Gene name", "source", "source version"]]
    genes["id"] = genes["subject"]
    genes["category"] = "biolink:Gene"
    genes["name"] = genes["Gene name"]

    nodes = pd.concat(
        [
            genes[
                ["id", "category", "name", "provided_by", "source", "source version"]
            ],
            ae[["id", "category", "name", "provided_by", "source", "source version"]],
        ]
    ).drop_duplicates()

    nodes[["id", "name", "category", "provided_by", "source", "source version"]].to_csv(
        f"{args.output[0]}", sep="\t", index=False
    )


if __name__ == "__main__":
    main()
