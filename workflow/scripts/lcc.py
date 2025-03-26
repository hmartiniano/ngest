# Import the argparse module for parsing command-line arguments.
import argparse
# Import the Counter class from the collections module for counting elements.
from collections import Counter
# Import the Transformer class from the kgx.transformer module for KG manipulation.
from kgx.transformer import Transformer
# Import the networkx module for graph analysis.
import networkx as nx


def get_parser():
    """
    Define and return the command-line argument parser.
    """
    # Create an ArgumentParser object.
    parser = argparse.ArgumentParser(
        prog="lcc.py",
        description=(
            "lcc: extract the largest connected component from a tsv format KG."
        ),
    )
    # Add an argument for the node file.
    parser.add_argument("-n", "--nodes", help="Node file")
    # Add an argument for the edge file.
    parser.add_argument("-e", "--edges", help="Edge files")
    # Add an argument for the output prefix with a default value.
    parser.add_argument(
        "-o", "--output", default="lcc", help="Output prefix. Default: lcc"
    )
    # Return the parser object.
    return parser


def main():
    """
    Main function to extract the largest connected component (LCC) from a graph.
    """
    # Get the command-line arguments.
    parser = get_parser()
    args = parser.parse_args()
    # Define input arguments for the transformer.
    input_args = {"filename": [args.nodes, args.edges], "format": "tsv"}
    # Define output arguments for the transformer.
    output_args = {"filename": args.output, "format": "tsv"}
    # Create a Transformer object.
    t = Transformer(stream=False)
    # Transform the input graph.
    t.transform(input_args=input_args)
    # Print the connected components and their sizes.
    print(
        "connected components:",
        Counter(map(len, nx.connected_components(t.store.graph.graph.to_undirected()))),
    )
    # Find the largest connected component (LCC).
    lcc = max(nx.connected_components(t.store.graph.graph.to_undirected()), key=len)
    print("Size of lcc:", len(lcc))  # Print the size of the LCC.
    # Set the graph to the LCC.
    t.store.graph.graph = t.store.graph.graph.subgraph(lcc)
    # Save the LCC to the specified output.
    t.save(output_args)


if __name__ == "__main__":
    main()

