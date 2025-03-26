"""
This script processes Ensembl data to map Ensembl gene IDs to Entrez Gene IDs.
It reads a TSV file, extracts the necessary columns, and outputs a new TSV 
file with Ensembl IDs and their corresponding Entrez Gene IDs.
"""
import argparse
import pandas as pd

# Define the column names for the output data.
ENSEMBL_COLUMNS = ["Ensembl ID", "Entrez Gene ID"]


def read_file(fname):
    """
    Reads an Ensembl data file, extracts the 'gene_stable_id' and 'xref' columns, 
    renames them, and returns a cleaned DataFrame.

    Args:
        fname (str): The path to the input TSV file.

    Returns:
        pd.DataFrame: A DataFrame containing Ensembl IDs and Entrez Gene IDs.
    """
    df = pd.read_csv(fname, sep="\t", low_memory=False)
    df = df[["gene_stable_id", "xref"]].drop_duplicates()
    df.columns = ENSEMBL_COLUMNS
    return df


def get_parser():    
    """
    Creates and configures an argument parser for the script.

    Returns:
        argparse.ArgumentParser: An argument parser instance.
    """
    parser = argparse.ArgumentParser(
        prog="ensembl_to_entrez.py",
        description="ensembl_to_entrez: download ensembl and entrez ids to csv file",
    )
    parser.add_argument("-i", "--input", help="Input files", required=True)
    parser.add_argument("-o", "--output", default="ensembl to entrez", help="Output ensembl data.")
    return parser


def main():
    """
    Main function to parse command-line arguments, read the input file, and write the output file.
    """
    parser = get_parser()
    args = parser.parse_args()
    ensemblf = read_file(args.input)
    ensemblf[["Entrez Gene ID", "Ensembl ID"]].to_csv(
        f"{args.output}", sep="\t", index=False
    )


if __name__ == "__main__":
    """
    Entry point of the script.
    """
    main()
