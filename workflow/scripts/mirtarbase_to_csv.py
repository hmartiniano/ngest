import argparse
import pandas as pd
from xlsx2csv import Xlsx2csv
from io import StringIO

# Define a function to get the command-line argument parser
def get_parser():
    parser = argparse.ArgumentParser(
        prog="mirtarbase_to_csv.py",
        description="mirtarbase_to_csv: convert a mirtarbase xlsx file to csv.",
    )
    # Add an argument for the input file
    parser.add_argument("-i", "--input", help="Input file")
    # Add an argument for the output prefix with a default value
    parser.add_argument(
        "-o", "--output", default="ensembl", help="Output prefix. Default: out"
    )
    return parser


def read_excel(path: str, sheet_name: str) -> pd.DataFrame:
    # Create a StringIO buffer to hold the CSV data
    buffer = StringIO()
    # Convert the specified sheet in the Excel file to CSV format and write it to the buffer
    Xlsx2csv(path, outputencoding="utf-8", sheet_name=sheet_name).convert(buffer)
    # Reset the buffer's position to the beginning
    buffer.seek(0)
    # Read the CSV data from the buffer into a pandas DataFrame
    df = pd.read_csv(buffer)
    return df


def main():
    parser = get_parser()
    # Parse the command-line arguments
    args = parser.parse_args()
    path = args.input
    sheet = "Homo sapiens"
    pd.read_excel(path, sheet, engine="openpyxl").to_csv(f"{args.output}", sep="\t", index=False)


if __name__ == "__main__":
    main()
