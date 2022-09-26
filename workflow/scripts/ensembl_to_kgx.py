import uuid
import json
import argparse
import pandas as pd



def read_files(fname):
    df = pd.read_csv(fname, sep="\t", comment="!", low_memory=False)
    return df


def transform_nodes(ensembl, uniprot):

    ensemblf = ensembl
    nodes = pd.DataFrame(columns=["provided_by", "id", "name", "category", "xref"])
    uniprotf = uniprot

    genes, rnas, proteins = [],[],[]

    for i in range(len(ensemblf)):

        geneinfo = {
            "provided_by" : "ENSEMBL",
            "id": "ENSEMBL:" + ensemblf["Gene ID"][i],
            "category": "biolink:Gene",
            "name": ensemblf["Gene Name"][i],
            "xref": ""
        }
        genes.append(geneinfo)

        #only RNACentral ID
        if ensemblf["RNACentral Id"][i] != "" and str(ensemblf["RNACentral Id"][i]) != "nan":
            rnainfo = {
                "provided_by": "ENSEMBL",
                "id": "RNACentral:" + ensemblf["RNACentral Id"][i],
                "category": "biolink:Transcript",
                "name": ensemblf["Transcript Name"][i],
                "xref": "ENSEMBL:" + ensemblf["Transcript ID"][i]
            }
            rnas.append(rnainfo)

        else:
            continue

        # ignores proteins without Uniprot ID
        if ensemblf["Uniprot ID"][i] != "" and str(ensemblf["Uniprot ID"][i]) != "nan":
            name = ""

            if ensemblf["Uniprot ID"][i] in uniprotf["Entry"].values:
                name = uniprotf[uniprotf['Entry'] == ensemblf["Uniprot ID"][i]]['Entry Name'].values[0]


            proteininfo = {
                "provided_by": "ENSEMBL",
                "id": "UniProtKB:" + str(ensemblf["Uniprot ID"][i]),
                "category": "biolink:Protein",
                "name": name,
                "xref": "ENSEMBL:" + ensemblf["Protein ID"][i]
            }
            proteins.append(proteininfo)

    nodes = pd.concat([pd.DataFrame(genes),pd.DataFrame(rnas),pd.DataFrame(proteins)]).drop_duplicates()
    return nodes

def transform_edges(ensemblf):

    ensemblf["FinalID"] = ensemblf["Gene ID"].apply(lambda x: uuid.uuid4())
    edges = pd.DataFrame(columns=["object", "subject", "id", "predicate", "provided by", "relation"])
    rnas, proteins = [], []

    for i in range(len(ensemblf)):
        if ensemblf["RNACentral Id"][i] != "" and str(ensemblf["RNACentral Id"][i]) != "nan":
            genetorna = {
                "object": "ENSEMBL:" + ensemblf["Gene ID"][i],
                "subject": "RNACentral:" + ensemblf["RNACentral Id"][i],
                "id": ensemblf['FinalID'],
                "predicate": "biolink:has_gene_product",
                "provided by": "ENSEMBL",
                "relation": "RO:0002511"
            }
            rnas.append(genetorna)

        if ensemblf["Uniprot ID"][i] != "" and str(ensemblf["Uniprot ID"][i]) != "nan":
            genetoprotein = {
                "object": "ENSEMBL:" + ensemblf["Gene ID"][i],
                "subject":"UniProtKB:" + str(ensemblf["Uniprot ID"][i]),
                "id": ensemblf['FinalID'],
                "predicate": "biolink:has_gene_product",
                "provided by" : "ENSEMBL",
                "relation": "RO:0002205"
            }
            proteins.append(genetoprotein)


    edges = pd.concat([pd.DataFrame(rnas), pd.DataFrame(proteins)])
    return edges



def get_parser():
    parser = argparse.ArgumentParser(prog="ensembl_to_kgx.py",
                                     description='ensembl_to_csv: convert an ensembl file to CSVs with nodes and edges.')
    parser.add_argument('-i', '--input', nargs="+", help="Input files")
    parser.add_argument('-o', '--output', nargs="+", default="ensembl", help="Output prefix. Default: out")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Transform nodes
    uniprotf = read_files(args.input[1])
    ensemblf = read_files(args.input[0])
    ensemblnodes = transform_nodes(ensemblf, uniprotf)
    ensemblnodes[["id", "name", "category", "provided_by", "xref"]].to_csv(f"{args.output [0]}", sep="\t", index=False)
    #Transform edges
    ensemblegdes = transform_edges(ensemblf)
    ensemblegdes[["object", "subject", "id", "predicate", "provided by", "relation"]].to_csv(
        f"{args.output[1]}", sep="\t", index=False)


if __name__ == '__main__':
    main()
