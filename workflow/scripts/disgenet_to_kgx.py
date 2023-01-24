import argparse
import pandas as pd
import uuid


def read_files(fname):
    df = pd.read_csv(fname, sep="\t", low_memory=False)
    return df

def get_version(fname):
    with open(fname) as f:
        for line in f:
            if "version" in line:
                version = line.split("version ")[1].split(").")[0]
    return version

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
    parser = get_parser()
    args = parser.parse_args()
    disgenet = read_files(args.input[0])
    disgenet_mapping = read_files(args.input[1])
    entrez_to_ensembl = (
        read_files(args.input[2]).drop_duplicates().set_index("Entrez Gene ID")
    )

    entrez_to_ensembl = entrez_to_ensembl[
        ~entrez_to_ensembl.index.duplicated(keep="first")
    ].iloc[:, 0]

    # Transform nodes
    disgenet_mapping = disgenet_mapping[
        disgenet_mapping["vocabulary"].isin(["HPO", "MONDO"])
    ]

    disgenet_mapping["code"] = (
        disgenet_mapping["vocabulary"] + ":" + disgenet_mapping["code"]
    ).str.replace("HPO:", "")
    disgenet_mapping = (
        disgenet_mapping[["diseaseId", "code"]].drop_duplicates().set_index("diseaseId")
    )
    disgenet_mapping = disgenet_mapping[
        ~disgenet_mapping.index.duplicated(keep="first")
    ].iloc[:, 0]

    disgenet["geneId"] = disgenet["geneId"].map(str)

    disgenet["object"] = disgenet["diseaseId"].map(disgenet_mapping)
    disgenet["subject"] = "ENSEMBL:" + disgenet["geneId"].map(entrez_to_ensembl)
    disgenet["provided_by"] = "Disgenet"
    disgenet["source"] = "Disgenet"
    disgenet["source version"] = get_version(args.version)

    disgenet = disgenet.dropna(subset=["object", "subject"])

    gene_to_phenotype = disgenet[disgenet.object.str.startswith("HP")]
    gene_to_phenotype["category"] = "biolink:GeneToPhenotypicFeatureAssociation"
    gene_to_phenotype["predicate"] = "biolink:associated_with"
    gene_to_phenotype["relation"] = "RO:0016001"
    gene_to_phenotype["knowledge_source"] = "Disgenet"

    gene_to_phenotype = gene_to_phenotype[
        [
            "subject",
            "predicate",
            "object",
            "category",
            "relation",
            "knowledge_source",
            "provided_by",
            "diseaseName",
            "source",
            "source version"
        ]
    ].drop_duplicates()
    gene_to_phenotype["id"] = gene_to_phenotype["subject"].apply(lambda x: uuid.uuid4())

    gene_to_disease = disgenet[disgenet.object.str.startswith("MONDO")]
    gene_to_disease["category"] = "biolink:GeneToDiseaseAssociation"
    gene_to_disease["predicate"] = "biolink:associated_with"
    gene_to_disease["relation"] = "RO:0016001"
    gene_to_disease["knowledge_source"] = "Disgenet"
    gene_to_disease = gene_to_disease[
        [
            "subject",
            "predicate",
            "object",
            "category",
            "relation",
            "knowledge_source",
            "provided_by",
            "diseaseName",
            "source",
            "source version"
        ]
    ].drop_duplicates()
    gene_to_disease["id"] = gene_to_disease["subject"].apply(lambda x: uuid.uuid4())

    edges = pd.concat([gene_to_phenotype, gene_to_disease])
    edges[
        [
            "id",
            "subject",
            "predicate",
            "object",
            "category",
            "relation",
            "knowledge_source",
            "source",
            "source version"
        ]
    ].drop_duplicates().to_csv(f"{args.output[1]}", sep="\t", index=False)

    phenotypes = gene_to_phenotype
    phenotypes["id"] = gene_to_phenotype["object"]
    phenotypes["category"] = "biolink:PhenotypicFeature"
    phenotypes["name"] = gene_to_phenotype["diseaseName"]
    phenotypes = phenotypes[["id", "category", "name", "provided_by", "source", "source version"]]

    diseases = gene_to_disease
    diseases["id"] = diseases["object"]
    diseases["category"] = "biolink:Disease"
    diseases["name"] = gene_to_disease["diseaseName"]
    diseases = diseases[["id", "category", "name", "provided_by", "source", "source version"]]

    nodes = disgenet
    nodes["id"] = disgenet["subject"]
    nodes["category"] = "biolink:Gene"
    nodes["name"] = disgenet["geneSymbol"]
    nodes = nodes[["id", "category", "name", "provided_by", "source", "source version"]]

    nodes = pd.concat([nodes, phenotypes, diseases]).drop_duplicates()

    nodes[["id", "name", "category", "provided_by", "source", "source version"]].to_csv(
        f"{args.output[0]}", sep="\t", index=False
    )


if __name__ == "__main__":
    main()
