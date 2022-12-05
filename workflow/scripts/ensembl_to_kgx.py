import uuid
import argparse
import pandas as pd

GENES = ["Gene Id", "Gene Version", "Gene Name"]


def read_id_mapping_uniprot(fname):
    df = pd.read_csv(fname, sep="\t", header=None, low_memory=False)
    df.columns = ["ID", "Database", "Database ID"]
    df = df[df["Database"] == "UniProtKB-ID"]
    df = df[["ID", "Database ID"]].drop_duplicates().set_index("ID")
    df = df[~df.index.duplicated(keep="first")].iloc[:, 0]
    return df


def read_genes(fname):
    df = pd.read_csv(fname, sep=";", low_memory=False, header=None)
    df = df.iloc[:, :3]
    df.columns = GENES
    df = df[df["Gene Name"].str.contains("gene_name")]
    df["Gene Id"] = "ENSEMBL:" + df["Gene Id"].str.split(" ").str[-1].str.replace(
        '"', ""
    )
    df["Gene Name"] = df["Gene Name"].str.split(" ").str[-1].str.replace('"', "")
    df = df[["Gene Id", "Gene Name"]].drop_duplicates().set_index("Gene Id")
    df = df[~df.index.duplicated(keep="first")].iloc[:, 0]
    return df


def get_parser():
    parser = argparse.ArgumentParser(
        prog="ensembl_to_kgx.py",
        description=(
            "ensembl_to_csv: convert an ensembl file to CSVs with nodes and edges."
        ),
    )
    parser.add_argument("-i", "--input", help="Input files")
    parser.add_argument("-u", "--uniprot", help="Input files")
    parser.add_argument("-g", "--genes", help="Input files")
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default="ensembl",
        help="Output prefix. Default: out",
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    uniprotf = read_id_mapping_uniprot(args.uniprot)
    ensemblf = pd.read_csv(args.input, sep="\t", comment="!", low_memory=False)
    genesf = read_genes(args.genes)

    ensemblf["protein name"] = ensemblf["xref"].map(uniprotf)
    ensemblf["provided_by"] = "ENSEMBL"
    ensemblf["knowledge_source"] = "ENSEMBL"
    ensemblf["protein name"] = ensemblf["xref"].map(uniprotf)

    gene_to_protein = ensemblf.dropna(subset=["xref"])
    gene_to_protein["subject"] = "ENSEMBL:" + gene_to_protein["gene_stable_id"]
    gene_to_protein["object"] = "UNIPROTKB:" + gene_to_protein["xref"]
    gene_to_protein["predicate"] = "biolink:has_gene_product"
    gene_to_protein["relation"] = "RO:0002205"
    gene_to_protein = gene_to_protein[
        ["subject", "predicate", "object", "relation", "knowledge_source"]
    ].drop_duplicates()
    gene_to_protein["id"] = gene_to_protein["subject"].apply(lambda x: uuid.uuid4())

    protein = ensemblf.dropna(subset=["xref"])

    protein["id"] = "UNIPROTKB:" + protein["xref"]
    protein["category"] = "biolink:Protein"
    protein["name"] = protein["protein name"]
    protein["xref"] = "ENSEMBL:" + ensemblf["protein_stable_id"]
    protein = protein[["id", "category", "name", "xref", "provided_by"]]

    edges = gene_to_protein

    genes = ensemblf
    genes["id"] = "ENSEMBL:" + ensemblf["gene_stable_id"]
    genes["category"] = "biolink:Gene"
    genes["name"] = genes["id"].map(genesf)
    genes = genes[["id", "category", "name", "provided_by"]]

    nodes = pd.concat([genes, protein]).drop_duplicates()

    nodes[["id", "name", "category", "provided_by", "xref"]].to_csv(
        f"{args.output [0]}", sep="\t", index=False
    )
    edges[
        ["object", "subject", "id", "predicate", "knowledge_source", "relation"]
    ].to_csv(f"{args.output[1]}", sep="\t", index=False)


if __name__ == "__main__":
    main()
