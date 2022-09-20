#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from dataclasses import dataclasses
import uuid
import json
import argparse
import pandas as pd


GAF_COLUMNS = [
    "DB",
    "DB Object ID",
    "DB Object Symbol",
    "Qualifier",
    "GO ID",
    "DB:Reference",
    "Evidence Code",
    "With (or) From",
    "Aspect",
    "DB Object Name",
    "DB Object Synonym",
    "DB Object Type",
    "Taxon(|taxon)",
    "Date",
    "Assigned By",
    "Annotation Extension",
    "Gene Product Form ID",
    ]

def read_gaf(fname):
    df = pd.read_csv(fname, sep="\t", comment="!", low_memory=False)
    df.columns = GAF_COLUMNS
    return df

def get_predicate_map(fname):
    ro = json.load(open(fname))
    predicate_to_relation = {}
    for node in ro["graphs"][0]["nodes"]:
        relation = node["id"] 
        predicate = node.get("lbl", None)
        if predicate is not None:
            relation = relation.split("/")[-1].replace("_", ":")
            predicate_to_relation[predicate.replace(" ", "_")] = relation
    return predicate_to_relation
    
def get_parser():
    parser = argparse.ArgumentParser(prog="goa_to_kgx.py", description='obo_to_csv: convert an obo file to CSVs with nodes and edges.')
    parser.add_argument('-i','--input', help="Input RO json file")
    parser.add_argument('-r','--ro', help="Input RO json file")
    parser.add_argument('-o','--output', default="goa", help="Output prefix. Default: out")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    #wget http://purl.obolibrary.org/obo/ro.json
    predicate_to_relation = get_predicate_map(args.ro)
    gaf = read_gaf(args.input) 
    gaf["provided_by"] = "goa"
    gaf["id"] = gaf.DB + ":" + gaf["DB Object ID"]
    gaf["category"] = "biolink:Protein"
    gaf["name"] = gaf["DB Object Symbol"]
    gaf[["id", "name", "category", "provided_by"]].to_csv(f"{args.output}_nodes.tsv", sep="\t", index=False)
    # Now edges
    gaf["object"] = gaf["GO ID"]
    gaf["subject"] = gaf.DB + ":" + gaf["DB Object ID"]
    gaf["id"] = gaf.id.apply(lambda x: uuid.uuid4())
    gaf["category"] = "biolink:FunctionalAssociation"
    gaf["negated"] = gaf.Qualifier.str.startswith("NOT|")
    gaf["predicate"] = "biolink:" + gaf.Qualifier.str.replace("NOT|", "", regex=False)
    gaf["relation"] = gaf.Qualifier.map(predicate_to_relation)
    gaf[["id", "subject", "predicate", "object", "category", "relation", "provided_by"]].to_csv(f"{args.output}_edges.tsv", sep="\t", index=False) 
    

if __name__ == '__main__':
    main()
