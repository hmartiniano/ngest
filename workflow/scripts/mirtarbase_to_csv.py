import argparse
import pandas as pd
from xlsx2csv import Xlsx2csv
from io import StringIO


def get_parser():
    parser = argparse.ArgumentParser(
        prog="mirtarbase_to_csv.py",
        description="mirtarbase_to_csv: convert a mirtarbase xlsx file to csv.",
    )
    parser.add_argument("-i", "--input", help="Input file")
    parser.add_argument(
        "-o", "--output", default="ensembl", help="Output prefix. Default: out"
    )
    return parser


def read_excel(path: str, sheet_name: str) -> pd.DataFrame:
    buffer = StringIO()
    Xlsx2csv(path, outputencoding="utf-8", sheet_name=sheet_name).convert(buffer)
    buffer.seek(0)
    df = pd.read_csv(buffer)
    return df


def main():
    parser = get_parser()
    args = parser.parse_args()
    path = args.input
    sheet = "Homo sapiens"
    pd.read_excel(path, sheet, engine="openpyxl").to_csv(f"{args.output}", sep="\t", index=False)


if __name__ == "__main__":
    main()
