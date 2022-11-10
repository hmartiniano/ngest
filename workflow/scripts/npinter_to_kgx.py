import argparse
import pandas as pd
import uuid

predicates = {
    "binding": "biolink:binds",
    "regulatory": "biolink:regulates",
    "expression correlation": "biolink:correlates",
    "coexpression": "biolink:coexpressed_with"
}

GENES = ["Gene Id",
         "Gene Version",
         "Gene Name"]

RNACENTRALMAPPING = ["RNACentral ID",
            "DB",
            "Transcript ID",
            "Species",
            "RNA Type",
            "Gene ID"]


def add_predicates(df):
    predicatef = pd.Series(predicates).drop_duplicates()
    df["predicate"] = df["class"].map(predicatef)
    return df

def read_rna(fname, type):
    df = pd.read_csv(fname, sep="\t", low_memory=False, header=None)
    df.columns = RNACENTRALMAPPING
    df["ID"] = df[type].str.split(".").str[0]
    df = df[["ID", "RNACentral ID"]].drop_duplicates().set_index("ID")
    df = df[~df.index.duplicated(keep='first')].iloc[:, 0]
    return df


def read_genes(fname):
    df = pd.read_csv(fname, sep=";", low_memory=False, header=None)
    df = df.iloc[:, :3]
    df.columns = GENES
    df = df[df["Gene Name"].str.contains("gene_name")]
    df["Gene Id"] = "ENSEMBL:" + df["Gene Id"].str.split(" ").str[-1].str.replace("\"", "")
    df["Gene Name"] = df["Gene Name"].str.split(" ").str[-1].str.replace("\"", "")
    df = df[["Gene Id", "Gene Name"]].drop_duplicates().set_index("Gene Name")
    df = df[~df.index.duplicated(keep='first')].iloc[:, 0]
    return df

def read_id_mapping_uniprot(fname):
    df = pd.read_csv(fname, sep="\t", header=None, low_memory=False)
    df.columns = ["ID", "Database", "Database ID"]
    df = df[df['Database'] == 'UniProtKB-ID']
    df = df[["ID", "Database ID"]].drop_duplicates().set_index("ID")
    df = df[~df.index.duplicated(keep='first')].iloc[:, 0]
    return df

def get_parser():
    parser = argparse.ArgumentParser(prog="bgee_to_kgx.py",
                                     description='bgee_to_csv: convert an bgee file to CSVs with nodes and edges.')
    parser.add_argument('-i', '--input', help="Input files")
    parser.add_argument('-p', '--proteins', help="Input files")
    parser.add_argument('-g', '--genes', help="Input files")
    parser.add_argument('-r', '--rna', help="Input files")
    parser.add_argument('-o', '--output', nargs="+", default="bgee", help="Output prefix. Default: out")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()

    npinterf = pd.read_csv(args.input, sep="\t", low_memory=False)
    npinterf = add_predicates(npinterf)
    uniprotf = read_id_mapping_uniprot(args.proteins)
    ensemblf = read_genes(args.genes)
    rnacentraltf = read_rna(args.rna, "Transcript ID")
    rnacentralgf = read_rna(args.rna, "Gene ID")

    npinterf["RNACentral Transcript"] = npinterf["ncID"].map(rnacentraltf)
    npinterf["RNACentral Gene"] = npinterf["ncID"].map(rnacentralgf)
    npinterf["subject"] = npinterf[["RNACentral Transcript", "RNACentral Gene"]].bfill(axis=1).iloc[:, 0]
    npinterf = npinterf.dropna(subset=["subject"])
    npinterf["subject"] = "RNACENTRAL:" + npinterf["subject"]
    npinterf["provided_by"] = "NPInter"
    npinterf["knowledge_source"] = "NPInter"

    npinterproteins = npinterf[npinterf["level"].isin(["RNA-Protein"])]
    npinterproteins["Uniprot Name"] = npinterproteins["tarID"].map(uniprotf)
    npinterproteins = npinterproteins.dropna(subset=["Uniprot Name"])
    npinterproteins["object"] = "UNIPROTKB:" + npinterproteins["tarID"]

    proteins = npinterproteins[["object", "provided_by", "Uniprot Name"]]
    proteins["id"] = proteins["object"]
    proteins["name"] = proteins["Uniprot Name"]
    proteins["category"] = "biolink:Protein"
    proteins = proteins[["id", "name", "provided_by", "category"]].drop_duplicates()

    npintergenes = npinterf[npinterf["level"].isin(["RNA-DNA"])]
    npintergenes["Ensembl ID"] = npintergenes["tarName"].map(ensemblf)
    npintergenes = npintergenes.dropna(subset=["Ensembl ID"])
    npintergenes["object"] = npintergenes["Ensembl ID"]

    genes = npintergenes[["object", "provided_by", "tarName"]]
    genes["id"] = genes["object"]
    genes["name"] = genes["tarName"]
    genes["category"] = "biolink:Gene"
    genes = genes[["id", "name", "provided_by", "category"]].drop_duplicates()

    rna = npinterf [["subject", "ncID", "provided_by", "ncName"]]
    rna["id"] = rna["subject"]
    rna["name"] = rna["ncName"]
    rna["category"] = "biolink:RNA"
    rna["xref"] = rna["ncID"]
    rna = rna[["id", "name", "provided_by", "category", "xref"]].drop_duplicates()

    nodes = pd.concat([proteins, genes, rna]).drop_duplicates()
    edges = pd.concat([npintergenes[["subject", "object", "knowledge_source", "predicate"]], npinterproteins[["subject", "object", "knowledge_source", "predicate"]]])
    edges["id"] = edges["subject"].apply(lambda x: uuid.uuid4())

    nodes.to_csv(f"{args.output[0]}", sep="\t", index=False)
    edges.to_csv(f"{args.output[1]}", sep="\t", index=False)

if __name__ == '__main__':
    main()