import uuid
import json

import argparse
import pandas as pd


def read_id_mapping_uniprot(fname):
    df = pd.read_csv(fname, sep="\t", header=None, low_memory=False)
    df.columns = ["ID", "Database", "Database ID"]
    df = df[df['Database'] == 'UniProtKB-ID']
    df = df[["ID", "Database ID"]].drop_duplicates().set_index("ID")
    df = df[~df.index.duplicated(keep='first')].iloc[:, 0]
    return df


def read_ensembl(fname):
    df = pd.read_csv(fname, sep="\t", comment="!", low_memory=False)
    return df


def read_id_mapping_rnacentral(fname):
    df = pd.read_csv(fname, sep=" ", header=None, low_memory=False)
    df.columns = ["ID", "Database", "Database ID", "Taxon", "Type", "Version"]
    return df


def transform_data(ensemblf, uniprotf, rnacentralf):
    # Transform nodes

    rnacentral_mapping =  rnacentralf[["ID", "Database ID"]].drop_duplicates().set_index("Database ID")
    rnacentral_mapping = rnacentral_mapping[~rnacentral_mapping.index.duplicated(keep='first')].iloc[:, 0]

    rnacentral_type = rnacentralf[["ID", "Type"]].drop_duplicates().set_index("ID")
    rnacentral_type = rnacentral_type[~rnacentral_type.index.duplicated(keep='first')].iloc[:, 0]


    ensemblf["transcript rnacentral"] =  ensemblf["RNACentral Id"].combine_first(ensemblf["Transcript ID"].map(rnacentral_mapping))
    ensemblf["protein name"] = ensemblf["Uniprot ID"].map(uniprotf)
    ensemblf["transcript type"] = ensemblf["transcript rnacentral"].map(rnacentral_type)
    ensemblf["provided_by"] = "ENSEMBL"


    gene_to_rna = ensemblf.dropna(subset=["transcript rnacentral"])
    gene_to_rna["subject"] = "ENSEMBL:" + gene_to_rna["Gene ID"]
    gene_to_rna["object"] = "RNACENTRAL:" + gene_to_rna["transcript rnacentral"]
    gene_to_rna['id'] = gene_to_rna["Gene ID"].apply(lambda x: uuid.uuid4())
    gene_to_rna["predicate"] = "biolink:has_gene_product"
    gene_to_rna["relation"] = "RO:0002511"
    gene_to_rna = gene_to_rna[
        ["id", "subject", "predicate", "object", "relation", "provided_by"]]


    rna = ensemblf.dropna(subset=["transcript rnacentral"])
    rna["id"] = "RNACENTRAL:" + rna["transcript rnacentral"]
    rna["category"] = "biolink:Transcript"
    rna["name"] = rna["Transcript Name"]
    rna["xref"] = "ENSEMBL:" + rna["Transcript ID"]
    rna["node_property"] = rna["transcript type"]
    rna = rna[["id", "category", "name", "xref", "node_property", "provided_by"]]

    gene_to_protein = ensemblf.dropna(subset=["Uniprot ID"])
    gene_to_protein['subject'] = "ENSEMBL:" + gene_to_protein["Gene ID"]
    gene_to_protein['object'] = "UniProtKB:" + gene_to_protein["Uniprot ID"]
    gene_to_protein['id'] = gene_to_protein["Gene ID"].apply(lambda x: uuid.uuid4())
    gene_to_protein["predicate"] = "biolink:has_gene_product"
    gene_to_protein["relation"] = "RO:0002205"
    gene_to_protein = gene_to_protein[
        ["id", "subject", "predicate", "object", "relation", "provided_by"]]

    protein = ensemblf.dropna(subset=["Uniprot ID"])

    protein["id"] = "UniProtKB:" + protein["Uniprot ID"]
    protein["category"] = "biolink:Protein"
    protein["name"] = protein["protein name"]
    protein["xref"] = "ENSEMBL:" + ensemblf["Protein ID"]
    protein = protein[["id", "category", "name", "xref", "provided_by"]]

    edges = pd.concat([gene_to_rna, gene_to_protein]).drop_duplicates()

    genes = ensemblf
    genes["id"] = "ENSEMBL:" + ensemblf["Gene ID"]
    genes["category"] = "biolink:Gene"
    genes["name"] = genes["Gene Name"]
    genes = genes[["id", "category", "name", "provided_by"]]

    nodes = pd.concat([genes, rna, protein]).drop_duplicates()

    return (nodes, edges)


def get_parser():
    parser = argparse.ArgumentParser(prog="ensembl_to_kgx.py",
                                     description='ensembl_to_csv: convert an ensembl file to CSVs with nodes and edges.')
    parser.add_argument('-i', '--input', nargs="+", help="Input files")
    parser.add_argument('-o', '--output', nargs="+", default="ensembl", help="Output prefix. Default: out")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    uniprotf = read_id_mapping_uniprot(args.input[1])
    ensemblf = read_ensembl(args.input[0])
    rnacentralf = read_id_mapping_rnacentral(args.input[2])

    # Transform nodes
    nodes, edges = transform_data(ensemblf, uniprotf, rnacentralf)
    nodes[["id", "name", "category", "provided_by", "xref", "node_property"]].to_csv(f"{args.output [0]}", sep="\t", index=False)
    edges[["object", "subject", "id", "predicate", "provided_by", "relation"]].to_csv(f"{args.output[1]}", sep="\t", index=False)


if __name__ == '__main__':
    main()
