#Not needed anymore


import argparse
import pandas as pd
import psycopg2
import psycopg2.extras

#url = "https://www.ebi.ac.uk/ebisearch/ws/rest/rnacentral?query=%RNA%20AND%20TAXONOMY:%229606%22&format=json"

RNA_COLUMNS = ["Upi",
               "Accession",
               "Database",
               "Feature Name",
               "Description",
               "Type"]


def get_parser():
    parser = argparse.ArgumentParser(prog="get_rnacentral_data_old.py", description='RNAcentral to tsv: download RNACentral tsv file')
    parser.add_argument('-o','--output', default="rnacentral", help="Output file.")
    return parser


def main():

    parser = get_parser()
    args = parser.parse_args()

    conn_string = "host='hh-pgsql-public.ebi.ac.uk' dbname='pfmegrnargs' user='reader' password='NWDMCE5xdipIjRrp'"
    conn = psycopg2.connect(conn_string, options='-c statement_timeout=300000000')
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = "select xref.upi, ac, rd.descr, ra.feature_name, ra.description, rna_type from xref left join rnc_accessions ra on ra.accession  = xref.ac left join rnc_database rd  on rd.id  = xref.dbid where xref.taxid = '9606'"

    cursor.execute(query)
    rnacentral = pd.DataFrame(cursor)
    rnacentral.columns = RNA_COLUMNS
    rnacentral[["Upi",
               "Accession",
               "Database",
               "Feature Name",
               "Description",
               "Type"]].to_csv(f"{args.output}", sep="\t", index=False)


if __name__ == '__main__':
    main()
