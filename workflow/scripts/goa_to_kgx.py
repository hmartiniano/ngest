import uuid
import json
import argparse
import pandas as pd
import yaml


GAF_COLUMNS = [
    "DB",
    "DB Object ID",
    "DB Object Symbol",
    "Qualifier",
    "GO ID",
    "DB:Reference",
    "Evidence Code",
    "With (or) From",
    "Aspect",
    "DB Object Name",
    "DB Object Synonym",
    "DB Object Type",
    "Taxon(|taxon)",
    "Date",
    "Assigned By",
    "Annotation Extension",
    "Gene Product Form ID",
]


def yaml_loader(fname):
    with open(fname) as f:
        classes = pd.DataFrame(yaml.full_load(f)["classes"])
    classes = classes.drop_duplicates().set_index("database")
    classes = classes[~classes.index.duplicated(keep="first")].iloc[:, 0]
    return classes


def read_gaf(fnames, biolinkclasses):
    gaf = pd.DataFrame(columns=GAF_COLUMNS)
    for f in fnames:
        df = pd.read_csv(f, sep="\t", comment="!", header=None, low_memory=False)
        df.columns = GAF_COLUMNS
        df["Qualifier"] = df["Qualifier"].replace("is_active_in", "active_in")
        df["Qualifier"] = df["Qualifier"].replace("NOT|is_active_in", "NOT|active_in")
        df["DB"] = df["DB"].str.upper()
        df["Biolink Category"] = df["DB"].map(biolinkclasses)
        gaf = pd.concat([gaf, df])
    return gaf


def get_predicate_map(fname):
    ro = json.load(open(fname))
    predicate_to_relation = {}
    for node in ro["graphs"][0]["nodes"]:
        relation = node["id"]
        if node.get("lbl", None) == "is active in":
            predicate = "active in"
        else:
            predicate = node.get("lbl", None)
        if predicate is not None:
            relation = relation.split("/")[-1].replace("_", ":")
            predicate_to_relation[predicate.replace(" ", "_")] = relation
    return predicate_to_relation


def get_parser():
    parser = argparse.ArgumentParser(
        prog="goa_to_kgx.py",
        description="goa_to_kgx: convert an goa file to CSVs with nodes and edges.",
    )
    parser.add_argument("-i", "--input", nargs="+", help="Input GAF files")
    parser.add_argument("-r", "--ro", help="Input RO json file")
    parser.add_argument("-g", "--go", help="Input GO nodes file")
    parser.add_argument("-c", "--cfg", help="Input config.yaml file")
    parser.add_argument(
        "-o", "--output", nargs="+", default="goa", help="Output prefix. Default: out"
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    biolinkclasses = yaml_loader(args.cfg)
    predicate_to_relation = get_predicate_map(args.ro)
    gof = pd.read_csv(args.go, sep="\t")[["id", "category", "name", "provided_by", "xref"]]
    gaf = read_gaf(args.input, biolinkclasses)
    gaf["provided_by"] = "GOA"
    gaf["id"] = gaf.DB + ":" + gaf["DB Object ID"].str.split("_").str[0]
    gaf["category"] = gaf["Biolink Category"]
    gaf["name"] = gaf["DB Object Symbol"]
    nodes=pd.concat([gaf[["id", "name", "category", "provided_by"]], gof])
    nodes.drop_duplicates().to_csv(
        f"{args.output[0]}", sep="\t", index=False
    )
    # Now edges
    gaf["object"] = gaf["GO ID"]
    gaf["subject"] = gaf.DB + ":" + gaf["DB Object ID"]
    gaf["category"] = "biolink:FunctionalAssociation"
    gaf["negated"] = gaf.Qualifier.str.startswith("NOT|")
    gaf["predicate"] = "biolink:" + gaf.Qualifier.str.replace("NOT|", "", regex=False)
    gaf["relation"] = gaf.Qualifier.map(predicate_to_relation)
    gaf["knowledge_source"] = "GOA"
    gaf = gaf[
        [
            "subject",
            "predicate",
            "object",
            "category",
            "negated",
            "relation",
            "knowledge_source",
        ]
    ].drop_duplicates()
    gaf["id"] = gaf.subject.apply(lambda x: uuid.uuid4())
    gaf.to_csv(f"{args.output[1]}", sep="\t", index=False)


if __name__ == "__main__":
    main()
