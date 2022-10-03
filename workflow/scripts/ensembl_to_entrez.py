import argparse
import pandas as pd
from pybiomart import Dataset

dataset = Dataset(name='hsapiens_gene_ensembl',
                  host='http://www.ensembl.org')

#dataset.list_attributes() to list all attributes available

ENSEMBL = (dataset.query(attributes=("entrezgene_id", "ensembl_gene_id"), use_attr_names=True)
                         .dropna()
                         .astype(int, errors="ignore")
                         .drop_duplicates())
ENSEMBL_COLUMNS = [
    "Entrez Gene ID",
    "Ensembl ID"
]

def ensembl_data():
    df = pd.DataFrame(ENSEMBL)
    df.columns = ENSEMBL_COLUMNS
    return df


def get_parser():
    parser = argparse.ArgumentParser(prog="ensembl_to_entrez.py", description='ensembl_to_entrez: download ensembl and entrez ids to csv file')
    parser.add_argument('-o','--output', default="ensembl to entrez", help="Output ensembl data.")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    ensemblf = ensembl_data()
    ensemblf[["Entrez Gene ID", "Ensembl ID"]].to_csv(f"{args.output}", sep="\t", index=False)


if __name__ == '__main__':
    main()