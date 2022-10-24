import json
import pandas as pd
import yaml
import requests
import argparse


class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)

def get_parser():
    parser = argparse.ArgumentParser(prog="get_db_versions.py",
                                     description='get_db_versions: get all databases versions.')
    parser.add_argument('-u', '--uniprot', help="UniprotKB version file")
    parser.add_argument('-e', '--ensembl', help="Ensembl version file")
    parser.add_argument('-r', '--rnacentral', help="RNACentral version file")
    parser.add_argument('-g', '--go', help="GO version file")
    parser.add_argument('-a', '--goa', help="GOA version file")
    parser.add_argument('-hp', '--hpoa', help="HPOA version file")
    parser.add_argument('-d', '--disgenet', help="Disgenet version file")
    parser.add_argument('-o', '--output', default="db_versions", help="Output prefix. Default: out")
    return parser


def main():
    versions = {}
    parser = get_parser()
    args = parser.parse_args()

    #ENSEMBL
    #ensembl = args.ensembl
    ensembl = "../data/raw/Homo_sapiens.GRCh38.108.uniprot.tsv.gz"
    version = ensembl.split(".")
    versions["ENSEMBL"] = version[3] + " " + version[4]

    #UNIPROT
    filef = pd.read_xml(args.uniprot)
    version = filef['version'].dropna().values[0]
    versions["UNIPROTKB"] = version

    #RNACENTRAL
    with open(args.rnacentral) as f:
        version = f.readlines()[1].split("\n")[0]
    versions["RNACENTRAL"] = version

    #GO
    with open(args.go, 'r') as f:
        version = json.load(f)['date']
    versions["GO"] = version

    #GOA
    with open(args.goa, 'r') as f:
        version = json.load(f)['date']
    versions["GOA"] = version

    #HPOA
    with open(args.hpoa) as f:
        for line in f:
            if '#date:' in line:
                version = line.split(':')[1].split("\n")[0].replace(" ", "")
    versions["HPOA"] = version

    #HP
    response = requests.get("https://api.github.com/repos/obophenotype/human-phenotype-ontology/releases/latest")
    version = response.json()["name"]
    versions["HP"] = version

    #MONDO
    response = requests.get("https://api.github.com/repos/monarch-initiative/mondo/releases/latest")
    version = response.json()["name"]
    versions["MONDO"] = version

    #UBERON
    response = requests.get("https://api.github.com/repos/obophenotype/uberon/releases/latest")
    version = response.json()["name"]
    versions["UBERON"] = version

    #CL
    response = requests.get("https://api.github.com/repos/obophenotype/cell-ontology/releases/latest")
    version = response.json()["name"]
    versions["CL"] = version


    #DISGENET
    with open(args.disgenet) as f:
        for line in f:
            if 'version' in line:
                version = line.split('version ')[1].split(').')[0]
    versions["DISGENET"] = version

    with open(args.output, 'w') as f:
         yaml.dump(versions, f, Dumper=Dumper)



if __name__ == '__main__':
    main()