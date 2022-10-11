import json
import pandas as pd
from pybiomart import Dataset, Server
import yaml
import requests


class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)


def yaml_version_update(fname, id, version):
    with open(fname) as f:
        doc = yaml.full_load(f)
    for database in doc['versions']:
        if database['database'] == id:
            database['version'] = version
    with open(fname, 'w') as f:
         yaml.dump(doc, f, Dumper=Dumper)

def get_ensembl_version(configf):
    server = Server(host='http://www.ensembl.org')
    version = server.list_marts()['display_name'][0]
    yaml_version_update(configf, "ENSEMBL", version)

def get_uniprot_version(configf, file):
    filef = pd.read_xml(file)
    version = filef['version'].dropna().values
    yaml_version_update(configf, "UNIPROTKB", version)

def get_rnacentral_version(configf, file):
    with open(file) as f:
        version = f.readlines()[1]
    yaml_version_update(configf, "RNACENTRAL", version)

def get_go_version(configf, file):
    with open(file, 'r') as f:
        version = json.load(f)['date']
    yaml_version_update(configf, "GO", version)

def get_goa_version(configf, file):
    with open(file, 'r') as f:
        version = json.load(f)['date']
    yaml_version_update(configf, "GOA", version)

def get_hpoa_version(configf, file):
    with open(file) as f:
        for line in f:
            if '#date:' in line:
                version = line.split(':')[1]
    yaml_version_update(configf, "HPOA", version)

def get_disgenet_version(configf, file):
    with open("/home/ana/PycharmProjects/ngest/data/raw/disgenet_readme.txt") as f:
        for line in f:
            if 'version' in line:
                version = line.split('version ')[1].split(').')[0]
    yaml_version_update(configf, "DISGENET", version)

def get_hpo_version(configf, file):
    response = requests.get("https://api.github.com/repos/obophenotype/human-phenotype-ontology/releases/latest")
    version = response.json()["name"]
    yaml_version_update(configf, "HPO", version)

def get_mondo_version(configf, file):
    response = requests.get("https://api.github.com/repos/monarch-initiative/mondo/releases/latest")
    version = response.json()["name"]
    yaml_version_update(configf, "MONDO", version)


