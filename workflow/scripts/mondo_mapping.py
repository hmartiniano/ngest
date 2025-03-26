import argparse
import pandas as pd


# Define a function to create an argument parser for the script.
def get_parser():
    """
    Creates an argument parser for the mondo_mapping script.

    Returns:
        argparse.ArgumentParser: An argument parser instance.
    """
    parser = argparse.ArgumentParser(
        prog="mondo_mapping.py", description="mondo_mapping: get mondo mapping csv file"
    )
    parser.add_argument("-i", "--input", help="Input mondo data file.")
    parser.add_argument("-o", "--output", default="mondo_mapping", help="Output mondo mapping.")
    return parser


# Define the main function of the script.
def main():
    """
    Main function to extract and map Mondo disease identifiers to external cross-references.
    """
    parser = get_parser()
    args = parser.parse_args()
    # Read the input JSON file into a pandas DataFrame and extract the 'nodes' data.
    mondo_nodes = pd.DataFrame(pd.read_json(args.input).graphs[0]["nodes"])
    # Clean the 'id' column by extracting the last part after '/', replacing '_' with ':'
    mondo_nodes["id"] = mondo_nodes["id"].str.split("/").str[-1].str.replace("_", ":", regex=False)
    # Copy the meta data in a new column
    mondo_nodes["xrefs"] = mondo_nodes["meta"]
    # Initialize an empty list to store the mappings.
    mondo_map = []

    # Iterate over each node in the DataFrame
    for node in range(len(mondo_nodes)):
        try:
            # Extract the 'xrefs' (cross-references) data from the 'meta' column of the current node.
            xrefs = mondo_nodes["meta"][node]["xrefs"]
            # Check if 'xrefs' exist for the current node.
            if xrefs is not None:
                # Iterate over each xref and append a tuple containing the xref value and the mondo id.
                for xref in xrefs:
                    mondo_map.append((xref["val"], mondo_nodes["id"][node]))
        except:
            # In case of error, skip this node
            continue
    # Transform the list of mappings into a DataFrame
    mondo_map = pd.DataFrame(mondo_map, columns=["disease", "mondo"])
    # Export into a tsv file
    mondo_map.to_csv(f"{args.output}", sep="\t", index=False)


if __name__ == "__main__":
    main()
