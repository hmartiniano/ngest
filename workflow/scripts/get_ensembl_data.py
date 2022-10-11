import uuid
import json
import argparse
import pandas as pd
from pybiomart import Dataset, Server
import yaml
import files_versions

dataset = Dataset(name='hsapiens_gene_ensembl',
                  host='http://www.ensembl.org')

#dataset.list_attributes() to list all attributes available

ENSEMBL = dataset.query(attributes=['ensembl_gene_id',
                                    'external_gene_name',
                                    'ensembl_transcript_id',
                                    'external_transcript_name',
                                    'rnacentral',
                                    'ensembl_peptide_id',
                                    'uniprotswissprot'])

ENSEMBL_COLUMNS = [
    "Gene ID",
    "Gene Name",
    "Transcript ID",
    "Transcript Name",
    "RNACentral Id",
    "Protein ID",
    "Uniprot ID"

]

def ensembl_data():
    df = pd.DataFrame(ENSEMBL)
    df.columns = ENSEMBL_COLUMNS
    return df


def get_parser():
    parser = argparse.ArgumentParser(prog="get_ensembl_data.py", description='ensembl to csv: download ensembl csv file')
    parser.add_argument('-c', '--cfg', help="Input config.yaml file")
    parser.add_argument('-o','--output', default="ensembl", help="Output ensembl data.")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    ensemblf = ensembl_data()
    files_versions.get_ensembl_version(args.cfg)
    ensemblf[["Gene ID",
    "Gene Name",
    "Transcript ID",
    "Transcript Name",
    "RNACentral Id",
    "Protein ID",
    "Uniprot ID"]].to_csv(f"{args.output}", sep="\t", index=False)


if __name__ == '__main__':
    main()

