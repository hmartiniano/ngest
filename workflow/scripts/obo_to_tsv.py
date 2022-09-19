#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from dataclasses import dataclasses
import obonet
import pandas as pd


whitelist_entities = ["GO", "CL", "HP", "Uberon", "Orphanet"]

def attribute_namespace(term_id):
    {"CL": "cell",
     "Uberon", "anatomical_entity",
     "HP", "phenotype",
     "MONDO": "disease",
     "Orphanet": "disease",
     "DOID", "disease",
    }

#@dataclass
class Ontology:
    def __init__(self, terms, relationships, name=None):
        self.terms = terms
        self.relationships = relationships
        self.name = name
        self.n_terms = terms.shape[0]
        self.n_relationships = relationships.shape[0]

    def dump(self, basename=None):
        basename = self.name if basename is None else basename 
        basename = "merged" if basename is None else basename
        self.terms.to_csv(basename + "_entities.csv", index=False, sep="\t")
        self.relationships.to_csv(basename + "_relationships.csv", index=False, sep="\t")

    def stats(self):
        print("name:", self.name)
        print("number of terms:", self.n_terms)
        print("number of relationships:", self.n_relationships)

    def identfy_relationships(self):
        namespaces = self.terms.namespace.unique().tolist()
        if not namespaces:
            self.terms["namespace"] = [self.name] * self.terms.shape[0]
        self.relationships["r"] = self.relationships 

    @classmethod
    def load(cls, url):
        graph = obonet.read_obo(url)
        terms = []
        for node, node_data in graph.nodes(data=True):
            node_data["term_id"] = node
            node_data["ontology"] = url
            terms.append(node_data)
        terms = pd.DataFrame(terms)
        relationships = pd.DataFrame(graph.edges(keys=True), columns=["h", "t", "r"])
        return Ontology(terms, relationships, name=url.split(".")[0])


def merge(o1, o2):
    merged = pd.merge(
        o1.terms.explode("xref"),
        o2.terms, 
        left_on="xref",
        right_on="term_id",
        how='left')
    #.sort_values('term_id').reset_index(drop=True)
    xref = "xref_x" if "xref_x" in merged.columns else "xref"
    mapping = merged[merged[xref] == merged.term_id_y][["term_id_x", "term_id_y"]]
    terms = pd.concat((o1.terms, o2.terms[~o2.terms.term_id.isin(mapping.term_id_y)]))
    relationships = pd.concat((o1.relationships, o2.relationships.replace(mapping.set_index("term_id_y"))))
    relationships.columns = ["h", "t", "r"]
    return Ontology(terms, relationships)

    #o1.terms["equivalence"] = o1.terms.xref.str.contains(o1.terms.term_id)
    #print(o1.terms.equivalence)


def get_parser()
    parser = argparse.ArgumentParser(prog = _program,
    description='obo_to_csv: convert an obo file to CSVs with nodes and edges.')
    parser.add_argument('-i','--input', help="Input OBO file")
    parser.add_argument('-o','--output', default="out", help="Output prefix. Default: out")
    return parser


def main()
    parser = get_parser()
    ontology = Ontology.load(args.input)
    ontology.dump(basename=args.output)

if __name__ == '__main__':
    main()
