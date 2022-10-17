import uuid
import argparse
import pandas as pd

HPOA_COLUMNS = [
    "DatabaseId",
    "DB Name",
    "Qualifier",
    "HPO ID",
    "DB Reference",
    "Evidence",
    "Onset",
    "Frequency",
    "Sex",
    "Modifier",
    "Aspect",
    "Biocuration"
    ]


def read_hpoa(fname):
    hpoa = pd.read_csv(fname, sep="\t", header=None, low_memory=False, comment='#')
    hpoa.columns = HPOA_COLUMNS
    return hpoa

def read_mondo(fname):
    mondo = pd.read_csv(fname, sep="\t", low_memory=False)
    mondo = mondo.drop_duplicates().set_index("disease")
    mondo = mondo[~mondo.index.duplicated(keep='first')].iloc[:, 0]
    return mondo

def get_parser():
    parser = argparse.ArgumentParser(prog="hpoa_to_kgx.py",
                                     description='hpoa_to_kgx: convert an hpoa file to CSVs with nodes and edges.')
    parser.add_argument('-i', '--input', help="Input hpoa files")
    parser.add_argument('-m', '--mapping', help="Input mondo mapping files")
    parser.add_argument('-o', '--output', nargs="+", default="goa", help="Output prefix. Default: out")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    hpoa = read_hpoa(args.input)
    mondo_mapping = read_mondo(args.mapping)

    hpoa["provided_by"] = "HPOA"
    hpoa["id"] = hpoa["DatabaseId"].map(mondo_mapping)
    hpoa["category"] = "biolink:Disease"
    hpoa["name"] = hpoa["DB Name"]
    hpoa[["id", "name", "category", "provided_by"]].dropna().drop_duplicates().to_csv(f"{args.output[0]}", sep="\t", index=False)
    # Now edges

    hpoa["subject"] = hpoa["DatabaseId"].map(mondo_mapping)
    hpoa["object"] = hpoa["HPO ID"]
    hpoa["id"] = hpoa.id.apply(lambda x: uuid.uuid4())
    hpoa["category"] = "biolink:DiseaseToPhenotypicFeatureAssociation"
    hpoa["negated"] = hpoa.Qualifier.str.startswith("NOT")
    hpoa["predicate"] = "biolink:has_phenotype"
    hpoa["relation"] = "RO:0002200"
    hpoa[["id", "subject", "predicate", "object","negated", "category", "relation", "provided_by"]].dropna().drop_duplicates().to_csv(f"{args.output[1]}",
                                                                                                sep="\t", index=False)


if __name__ == '__main__':
    main()
