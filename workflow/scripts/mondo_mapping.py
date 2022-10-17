import argparse
import pandas as pd

def get_parser():
    parser = argparse.ArgumentParser(prog="mondo_mapping.py", description='mondo_mapping: get mondo mapping csv file')
    parser.add_argument('-i', '--input', help="Input mondo data file.")
    parser.add_argument('-o', '--output', default="mondo_mapping", help="Output mondo mapping.")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    mondo_nodes = pd.DataFrame(pd.read_json(args.input).graphs[0]["nodes"])
    mondo_nodes["id"] = mondo_nodes["id"].str.split("/").str[-1].str.replace('_', ':', regex=False)
    mondo_nodes["xrefs"] =  mondo_nodes["meta"]
    mondo_map = []

    for node in range(len(mondo_nodes)):
        try:
            xrefs = mondo_nodes["meta"][node]["xrefs"]
            if xrefs is not None:
                for xref in xrefs:
                    mondo_map.append((xref["val"], mondo_nodes["id"][node]))
        except:
            continue
    mondo_map = pd.DataFrame(mondo_map, columns=["disease", "mondo"])
    mondo_map.to_csv(f"{args.output}", sep="\t", index=False)

if __name__ == '__main__':
    main()