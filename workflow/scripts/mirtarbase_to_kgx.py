import uuid
import argparse
import pandas as pd
from xlsx2csv import Xlsx2csv
from io import StringIO



def get_parser():
    parser = argparse.ArgumentParser(prog="mirtarbase_to_kgx.py",
                                     description='mirtarbase_to_kgx: convert a mirtarbase file to CSVs with nodes and edges.')
    parser.add_argument('-i', '--input', help="Input files")
    parser.add_argument('-r', '--rna', help="Input files")
    parser.add_argument('-g', '--genes', help="Input files")
    parser.add_argument('-o', '--output', nargs="+", default="ensembl", help="Output prefix. Default: out")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    rnamapping = pd.read_csv(args.rna, sep="\t", header=None, low_memory=False).iloc[:, :5]
    rnamapping.columns =["RNACentral", "DB", "xref", "Species", "Type"]
    rnamapping = rnamapping[["RNACentral", "xref"]].drop_duplicates().set_index("xref")
    rnamapping = rnamapping[~rnamapping.index.duplicated(keep='first')].iloc[:, 0]

    genemapping = pd.read_csv(args.genes, sep="\t", low_memory=False).drop_duplicates().set_index("Entrez Gene ID")
    genemapping = genemapping[~genemapping.index.duplicated(keep='first')].iloc[:, 0]

    mirtarbase = pd.read_csv(args.input, sep="\t", low_memory=False)
    mirtarbase = mirtarbase[["miRTarBase ID", "miRNA", "Target Gene", "Target Gene (Entrez ID)"]]

    mirtarbase["object"] = mirtarbase["Target Gene (Entrez ID)"].map(str).map(genemapping)
    mirtarbase["subject"] = mirtarbase["miRNA"].map(rnamapping)
    mirtarbase = mirtarbase.dropna(subset=["object", "subject"])

    mirtarbase["object"] = "ENSEMBL:" + mirtarbase["object"]
    mirtarbase["subject"] = "RNACENTRAL:" + mirtarbase["subject"]
    mirtarbase ["provided_by"] = "Mirtarbase"
    mirtarbase["knowledge_source"] = "Mirtarbase"
    mirtarbase["predicate"] = "biolink:interacts_with"
    mirtarbase["relation"] = "RO:0002434"
    edges = mirtarbase[["object", "subject", "predicate", "knowledge_source", "relation"]].drop_duplicates()
    edges["id"] = mirtarbase['subject'].apply(lambda x: uuid.uuid4())


    rna = mirtarbase[["subject", "miRNA", "provided_by"]]
    rna["id"] = rna["subject"]
    rna["xref"] = rna["miRNA"]
    rna["category"] = "biolink:RNA"

    dna = mirtarbase[["object", "Target Gene", "provided_by", "Target Gene (Entrez ID)"]]
    dna["xref"] = dna["Target Gene (Entrez ID)"]
    dna["name"] = dna["Target Gene"]
    dna["category"] = "biolink:Gene"
    dna["id"] = dna["object"]

    nodes = pd.concat([dna, rna]).drop_duplicates()

    nodes[["id", "name", "category", "provided_by", "xref"]].to_csv(f"{args.output [0]}", sep="\t", index=False)
    edges.to_csv(f"{args.output[1]}", sep="\t", index=False)


if __name__ == '__main__':
    main()
