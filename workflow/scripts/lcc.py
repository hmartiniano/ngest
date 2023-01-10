import argparse
from collections import Counter
from kgx.transformer import Transformer
import networkx as nx

def get_parser():
    parser = argparse.ArgumentParser(
        prog="lcc.py",
        description=(
            "lcc: extract the largest connected component from a tsv format KG."
        ),
    )
    parser.add_argument("-n", "--nodes", help="Node file")
    parser.add_argument("-e", "--edges", help="Edge files")
    parser.add_argument("-o", "--output", default="lcc", help="Output prefix. Default: lcc")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    input_args = {'filename': [args.nodes, args.edges], 'format': 'tsv'}
    output_args = {'filename': args.output, 'format': 'tsv'}
    t = Transformer(stream=False)
    t.transform(input_args=input_args)
    print("connected components:", Counter(map(len, nx.connected_components(t.store.graph.graph.to_undirected()))))
    lcc = max(nx.connected_components(t.store.graph.graph.to_undirected()), key=len)
    print("Size of lcc:", len(lcc))
    t.store.graph.graph = t.store.graph.graph.subgraph(lcc)
    t.save(output_args)


if __name__ == "__main__":
    main()
