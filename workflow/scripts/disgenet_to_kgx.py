import argparse
import pandas as pd
import uuid

def read_files(fname):
    df = pd.read_csv(fname, sep="\t", low_memory=False)
    return df

def get_parser():
    parser = argparse.ArgumentParser(prog="disgenet_to_kgx.py",
                                     description='disgenet_to_csv: convert an disgenet file to CSVs with nodes and edges.')
    parser.add_argument('-i', '--input', nargs="+", help="Input files")
    parser.add_argument('-o', '--output', nargs="+", default="disgenet", help="Output prefix. Default: out")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    disgenet = read_files(args.input[0])
    disgenetmapping = read_files(args.input[1])
    entrez_to_ensembl = read_files(args.input[2]).drop_duplicates().set_index("Entrez Gene ID")
    entrez_to_ensembl = entrez_to_ensembl[~entrez_to_ensembl.index.duplicated(keep='first')].iloc[:, 0]

    # Transform nodes
    disgenetmapping = disgenetmapping[disgenetmapping["vocabulary"].isin(["HPO", "MONDO"])]

    disgenetmapping["code"] = (disgenetmapping["vocabulary"] + ":" + disgenetmapping["code"]).str.replace("HPO:", "")
    disgenetmapping = disgenetmapping[["diseaseId", "code"]].drop_duplicates().set_index("diseaseId")
    disgenetmapping = disgenetmapping[~disgenetmapping.index.duplicated(keep='first')].iloc[:, 0]

    disgenet["subject"] = disgenet["diseaseId"].map(disgenetmapping)
    disgenet["object"] = "ENSEMBL:" + disgenet["geneId"].map(entrez_to_ensembl)
    disgenet["provided_by"] = "Disgenet"

    disgenet = disgenet.dropna(subset=["object", "subject"])

    gene_to_phenotype = disgenet[disgenet.subject.str.startswith("HP")]
    gene_to_phenotype["category"] = "biolink:GeneToPhenotypicFeatureAssociation"
    gene_to_phenotype['id'] = gene_to_phenotype['object'].apply(lambda x: uuid.uuid4())
    gene_to_phenotype["predicate"] = "biolink:associated_with"
    gene_to_phenotype["relation"] = "RO:0016001"
    gene_to_phenotype = gene_to_phenotype[["id", "subject", "predicate", "object", "category", "relation", "provided_by", "diseaseName"]]

    phenotypes = gene_to_phenotype
    phenotypes["id"] = gene_to_phenotype["subject"]
    phenotypes["category"] = "biolink:PhenotypicFeature"
    phenotypes["name"] = gene_to_phenotype["diseaseName"]
    phenotypes = phenotypes[["id","category","name","provided_by"]]

    gene_to_disease = disgenet[disgenet.subject.str.startswith("MONDO")]
    gene_to_disease['object'] = gene_to_disease["object"]
    gene_to_disease['subject'] = gene_to_disease["subject"]
    gene_to_disease["category"] = "biolink:GeneToDiseaseAssociation"
    gene_to_disease['id'] = gene_to_disease['object'].apply(lambda x: uuid.uuid4())
    gene_to_disease["predicate"] = "biolink:associated_with"
    gene_to_disease["relation"] = "RO:0016001"
    gene_to_disease = gene_to_disease[["id", "subject", "predicate", "object", "category", "relation", "provided_by", "diseaseName"]]

    diseases = gene_to_disease
    diseases["id"] = diseases["subject"]
    diseases["category"] = "biolink:Disease"
    diseases["name"] = gene_to_disease["diseaseName"]
    diseases = diseases[["id","category","name","provided_by"]]

    edges = pd.concat([gene_to_phenotype, gene_to_disease])

    nodes = disgenet
    nodes["id"] = disgenet["object"]
    nodes["category"] = "biolink:Gene"
    nodes["name"] = disgenet["geneSymbol"]
    nodes = nodes[["id","category","name","provided_by"]]

    nodes = pd.concat([nodes, phenotypes, diseases])


    edges[["id", "subject", "predicate", "object", "category", "relation", "provided_by"]].to_csv(
        f"{args.output[1]}", sep="\t", index=False)

    nodes[["id", "name", "category", "provided_by"]].to_csv(f"{args.output[0]}", sep="\t", index=False)




if __name__ == '__main__':
    main()