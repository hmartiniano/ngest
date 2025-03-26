# Import necessary libraries
import uuid
import argparse
import pandas as pd


def get_parser():
    """Define and get command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="mirtarbase_to_kgx.py",
        description=(
            "mirtarbase_to_kgx: convert a mirtarbase file to CSVs with nodes and edges."
        ),
    )
    parser.add_argument("-i", "--input", help="Input files")
    parser.add_argument("-r", "--rna", help="Input files")
    parser.add_argument("-g", "--genes", help="Input files")
    parser.add_argument("-v", "--version", help="Database version")
    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        default="ensembl",
        help="Output prefix. Default: out",
    )
    return parser


def main():
    """Main function to process mirtarbase data and generate KGX node and edge files."""
    # Get command line arguments
    parser = get_parser()
    args = parser.parse_args()

    # Extract database version
    version = args.version

    # Load RNA mapping data
    rnamapping = pd.read_csv(args.rna, sep="\t", header=None, low_memory=False).iloc[
        :, :5
    ]
    
    rnamapping.columns = ["RNACentral", "DB", "xref", "Species", "Type"]
    # Preprocess RNA mapping: select columns, drop duplicates, set index, and remove duplicates
    rnamapping = rnamapping[["RNACentral", "xref"]].drop_duplicates().set_index("xref")
    rnamapping = rnamapping[~rnamapping.index.duplicated(keep="first")].iloc[:, 0]

    genemapping = (
        pd.read_csv(args.genes, sep="\t", low_memory=False)
        .drop_duplicates()
        .set_index("Entrez Gene ID")
    )
    # preprocess gene mapping: remove duplicates and set index
    genemapping = genemapping[~genemapping.index.duplicated(keep="first")].iloc[:, 0]

    # Load mirtarbase data
    mirtarbase = pd.read_csv(args.input, low_memory=False)
    
    # Select relevant columns from mirtarbase
    mirtarbase = mirtarbase[
        ["miRTarBase ID", "miRNA", "Target Gene", "Target Gene (Entrez ID)"]
    ]

    # Map target genes and miRNAs to identifiers
    mirtarbase["object"] = (
        mirtarbase["Target Gene (Entrez ID)"].map(str).map(genemapping)
    )
    mirtarbase["subject"] = mirtarbase["miRNA"].map(rnamapping) 
    mirtarbase = mirtarbase.dropna(subset=["object", "subject"])

    mirtarbase["object"] = "ENSEMBL:" + mirtarbase["object"]
    mirtarbase["subject"] = "RNACENTRAL:" + mirtarbase["subject"]
    mirtarbase["provided_by"] = "Mirtarbase"
    mirtarbase["knowledge_source"] = "Mirtarbase"
    mirtarbase["predicate"] = "biolink:interacts_with"
    mirtarbase["relation"] = "RO:0002434"
    mirtarbase["source"] = "Mirtarbase"
    mirtarbase["source version"] = version

    # Create edges dataframe
    edges = mirtarbase[
        [
            "object",
            "subject",
            "predicate",
            "knowledge_source",
            "relation",
            "source",
            "source version",
        ]
    ].drop_duplicates()
    edges["id"] = mirtarbase["subject"].apply(lambda x: uuid.uuid4())

    # Create RNA nodes dataframe
    rna = mirtarbase[["subject", "miRNA", "provided_by", "source", "source version"]]
    rna["id"] = rna["subject"]
    rna["xref"] = rna["miRNA"]
    rna["category"] = "biolink:RNAProduct"

    # Create DNA nodes dataframe
    dna = mirtarbase[
        [
            "object",
            "Target Gene",
            "provided_by",
            "Target Gene (Entrez ID)",
            "source",
            "source version",
        ]
    ]
    dna["xref"] = dna["Target Gene (Entrez ID)"]
    dna["name"] = dna["Target Gene"]
    dna["category"] = "biolink:Gene"
    dna["id"] = dna["object"]

    # Concatenate RNA and DNA nodes into a single dataframe
    nodes = pd.concat([dna, rna]).drop_duplicates()

    # Save nodes and edges to TSV files
    nodes[
        ["id", "name", "category", "provided_by", "xref", "source", "source version"]
    ].to_csv(f"{args.output [0]}", sep="\t", index=False)
    edges.to_csv(f"{args.output[1]}", sep="\t", index=False)

# execute the code if it is run as main script
if __name__ == "__main__":
    main()
