import argparse
import pandas as pd
import uuid


def read_id_mapping_uniprot(fname, id, type):
    df = pd.read_csv(fname, sep="\t", header=None, low_memory=False)
    df.columns = ["ID", "Database", "Database ID"]
    df = df[df['Database'] == type]
    df = df[["ID", "Database ID"]].drop_duplicates().set_index(id)
    df = df[~df.index.duplicated(keep='first')].iloc[:, 0]
    return df

def get_parser():
    parser = argparse.ArgumentParser(prog="stringdb_to_kgx.py",
                                     description='string_to_csv: convert an string file to CSVs with nodes and edges.')
    parser.add_argument('-i', '--input', help="Input files")
    parser.add_argument('-p', '--proteins', help="Input files")
    parser.add_argument('-o', '--output', nargs="+", default="string", help="Output prefix. Default: out")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()

    stringdbf = pd.read_csv(args.input, sep=" ", low_memory=False)
    idmapping = read_id_mapping_uniprot(args.proteins, "Database ID", "STRING")
    namemapping = read_id_mapping_uniprot(args.proteins,"ID", "UniProtKB-ID")
    stringdbf["protein1 id"] = stringdbf["protein1"].map(idmapping)
    stringdbf["protein2 id"] = stringdbf["protein2"].map(idmapping)

    stringdbf = stringdbf.dropna(subset=["protein1 id", "protein2 id"])
    stringdbf["subject"] = "UNIPROTKB:" + stringdbf["protein1 id"]
    stringdbf["object"] = "UNIPROTKB:" + stringdbf["protein2 id"]
    stringdbf["provided_by"] = "STRING"
    stringdbf["knowledge_source"] = "STRING"
    stringdbf["predicate"] = "biolink:interacts_with"
    stringdbf["relation"] = "RO:0002436"
    stringdbf["category"] = "biolink:Protein"
    stringdbf["has_confidence_level"] = stringdbf["combined_score"]

    protein1 = stringdbf[["protein1", "protein1 id", "subject", "provided_by", "category"]]
    protein1["id"] = protein1["subject"]
    protein1["name"] = protein1["protein1 id"].map(namemapping)
    protein1["xref"] = protein1["protein1"].str.split(".").str[-1]
    protein1 = protein1[["id", "name", "provided_by", "category", "xref"]]
    protein2 = stringdbf[["protein2", "protein2 id", "object", "provided_by", "category"]]
    protein2["id"] = protein2["object"]
    protein2["name"] = protein2["protein2 id"].map(namemapping)
    protein2["xref"] = protein2["protein2"].str.split(".").str[-1]
    protein2=protein2[["id", "name", "provided_by", "category", "xref"]]

    nodes = pd.concat([protein1, protein2]).drop_duplicates()

    edges = stringdbf[["subject", "object", "knowledge_source", "predicate", "has_confidence_level"]].drop_duplicates()
    edges["id"] = edges["subject"].apply(lambda x: uuid.uuid4())

    nodes.to_csv(f"{args.output[0]}", sep="\t", index=False)
    edges.to_csv(f"{args.output[1]}", sep="\t", index=False)

if __name__ == '__main__':
    main()