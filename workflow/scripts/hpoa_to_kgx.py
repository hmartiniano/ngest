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
    "Biocuration",
]

# Get version from the hpoa file

def get_version(fname):
    with open(fname) as f:
        for line in f:
            if "#version:" in line:
                version = line.split(":")[1].split("\n")[0].replace(" ", "")
    return version

# Read hpoa file
def read_hpoa(fname):
    hpoa = pd.read_csv(fname, sep="\t", header=None, low_memory=False, comment="#")
    hpoa.columns = HPOA_COLUMNS
    hpoa = hpoa[hpoa["DatabaseId"] != "database_id"].copy()
    return hpoa


# Read mondo file

def read_mondo(fname):
    mondo = pd.read_csv(fname, sep="\t", low_memory=False)
    mondo = mondo.drop_duplicates().set_index("disease")
    mondo = mondo[~mondo.index.duplicated(keep="first")].iloc[:, 0]
    return mondo


# Get parser for the command line arguments
def get_parser():
    parser = argparse.ArgumentParser(
        prog="hpoa_to_kgx.py",
        description="hpoa_to_kgx: convert an hpoa file to CSVs with nodes and edges.",
    )
    parser.add_argument("-i", "--input", help="Input hpoa files")
    parser.add_argument("-m", "--mapping", help="Input mondo mapping files")
    parser.add_argument("-n", "--hpo", help="Input hpo nodes")
    parser.add_argument(
        "-o", "--output", nargs="+", default="goa", help="Output prefix. Default: out"
    )
    return parser


# Main function to convert hpoa to kgx
def main():
    # Get arguments from command line
    parser = get_parser()
    args = parser.parse_args()
    # read hpoa and mondo mapping
    hpoa = read_hpoa(args.input)
    mondo_mapping = read_mondo(args.mapping)

    # get version from file
    version = get_version(args.input)

    # Add some columns to the hpoa dataframe
    hpoa["provided_by"] = "HPOA"
    hpoa["knowledge_source"] = "HPOA"
    hpoa["id"] = hpoa["DatabaseId"].map(mondo_mapping)
    hpoa["category"] = "biolink:Disease"
    hpoa["name"] = hpoa["DB Name"]
    hpoa["source"] = "HPOA"
    hpoa["source version"] = version    
    
    # Load hpo file and select some columns
    hpf = pd.read_csv(args.hpo, sep="\t")[
        ["id", "name", "category", "provided_by", "xref", "source", "source version"]
    ]
    hpf = hpf[hpf.id.str.startswith("HP")]
    nodes = (
        pd.concat(
            [
                hpoa[
                    [
                        "id",
                        "name",
                        "category",
                        "provided_by",
                        "source",
                        "source version",
                    ]
                ].dropna(subset=["id"]),
                hpf,
            ]
        )
        .drop_duplicates()
        .to_csv(f"{args.output[0]}", sep="\t", index=False, lineterminator="\n")
    )    

    # process edges
    hpoa["subject"] = hpoa["DatabaseId"].map(mondo_mapping)
    hpoa["object"] = hpoa["HPO ID"]
    hpoa["category"] = "biolink:DiseaseToPhenotypicFeatureAssociation"
    hpoa["negated"] = hpoa["Qualifier"].fillna("").str.startswith("NOT")
    hpoa["predicate"] = "biolink:has_phenotype"
    hpoa["relation"] = "RO:0002200"

    def extract_pmids(ref):
        if pd.isna(ref):
            return ""
        parts = str(ref).split(";")
        pmids = [p.strip() for p in parts if p.strip().startswith("PMID:") and p.strip()[5:].isdigit()]
        return "|".join(pmids)

    hpoa["publications"] = hpoa["DB Reference"].apply(extract_pmids)

    hpoa = hpoa.dropna(subset=["subject", "object"])

    edge_cols = [
        "subject",
        "predicate",
        "object",
        "negated",
        "category",
        "relation",
        "knowledge_source",
        "source",
        "source version",
    ]
    edges = (
        hpoa.groupby(edge_cols)["publications"]
        .apply(lambda s: "|".join(sorted(set(p for item in s for p in item.split("|") if p))[:50]))
        .reset_index()
    )
    edges["id"] = edges["subject"].apply(lambda x: uuid.uuid4())
    edges[
        [
            "subject",
            "predicate",
            "object",
            "negated",
            "category",
            "relation",
            "publications",
            "knowledge_source",
            "source",
            "source version",
            "id",
        ]
    ].to_csv(f"{args.output[1]}", sep="\t", index=False, lineterminator="\n")


# Run the main function
if __name__ == "__main__":
    main()
