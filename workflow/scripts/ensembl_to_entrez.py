import argparse
import pandas as pd

ENSEMBL_COLUMNS = ["Ensembl ID", "Entrez Gene ID"]


def read_file(fname):
    df = pd.read_csv(fname, sep="\t", low_memory=False)
    df = df[["gene_stable_id", "xref"]].drop_duplicates()
    df.columns = ENSEMBL_COLUMNS
    return df


def get_parser():
    parser = argparse.ArgumentParser(
        prog="ensembl_to_entrez.py",
        description="ensembl_to_entrez: download ensembl and entrez ids to csv file",
    )
    parser.add_argument("-i", "--input", help="Input files")
    parser.add_argument(
        "-o", "--output", default="ensembl to entrez", help="Output ensembl data."
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    ensemblf = read_file(args.input)
    ensemblf[["Entrez Gene ID", "Ensembl ID"]].to_csv(
        f"{args.output}", sep="\t", index=False
    )


if __name__ == "__main__":
    main()
