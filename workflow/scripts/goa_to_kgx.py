# Import necessary libraries for data processing, file handling, and command-line arguments
import uuid
import json
import argparse
import pandas as pd
import yaml

####################################################################
# Constants and Configurations
####################################################################

# Define the column names for GAF (Gene Association Format) files
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

####################################################################
# Data Loading and Preprocessing Functions
####################################################################

# Function to load YAML configuration file
def yaml_loader(fname):
    """
    Loads a YAML configuration file and extracts database-class mappings.
    """
    with open(fname) as f:
        # Load the YAML content into a DataFrame
        classes = pd.DataFrame(yaml.full_load(f)["classes"])
    # Remove duplicate entries and set 'database' column as index
    classes = classes.drop_duplicates().set_index("database")
    # Keep only the first occurrence of each database and select the first column
    classes = classes[~classes.index.duplicated(keep="first")].iloc[:, 0]
    return classes

# Function to read GAF files and process data
# This function reads GAF files, normalizes data, and maps databases to Biolink categories.
def read_gaf(fnames, biolinkclasses):
    """
    Reads multiple GAF files, processes them, and combines them into a single DataFrame.
    """
    # Initialize an empty DataFrame with GAF_COLUMNS
    gaf = pd.DataFrame(columns=GAF_COLUMNS)
    for f in fnames:
        # Read each file into a DataFrame, skipping comment lines and specifying no header
        df = pd.read_csv(f, sep="\t", comment="!", header=None, low_memory=False)
        # Set column names
        df.columns = GAF_COLUMNS
        # Normalize "Qualifier" column values
        df["Qualifier"] = df["Qualifier"].replace("is_active_in", "active_in")
        df["Qualifier"] = df["Qualifier"].replace("NOT|is_active_in", "NOT|active_in")
        # Convert database names to uppercase
        df["DB"] = df["DB"].str.upper()
        # Map databases to their corresponding Biolink categories
        df["Biolink Category"] = df["DB"].map(biolinkclasses)
        # Concatenate the current DataFrame to the main DataFrame
        gaf = pd.concat([gaf, df])
    return gaf

# Function to create a mapping from predicate to relation
# This function extracts predicate-to-relation mappings from a JSON file (RO).
def get_predicate_map(fname):
    """
    Extracts predicate-to-relation mapping from a JSON file (RO).
    """
    ro = json.load(open(fname))
    predicate_to_relation = {}
    for node in ro["graphs"][0]["nodes"]:
        relation = node["id"]
        if node.get("lbl", None) == "is active in":
            predicate = "active in"
        else:
            predicate = node.get("lbl", None)
        if predicate is not None:
            relation = relation.split("/")[-1].replace("_", ":")
            predicate_to_relation[predicate.replace(" ", "_")] = relation
    return predicate_to_relation

####################################################################
# Argument Parsing and Setup
####################################################################

# Function to set up the command-line argument parser
def get_parser():
    """
    Sets up the command-line argument parser for the script.
    """
    parser = argparse.ArgumentParser(
        prog="goa_to_kgx.py",
        description="goa_to_kgx: convert an goa file to CSVs with nodes and edges.",
    )
    # Define the arguments that the script can receive
    parser.add_argument("-i", "--input", nargs="+", help="Input GAF files")
    parser.add_argument("-r", "--ro", help="Input RO json file")
    parser.add_argument("-g", "--go", help="Input GO nodes file")
    parser.add_argument("-c", "--cfg", help="Input config.yaml file")
    parser.add_argument("-v", "--version", help="Input version file")
    parser.add_argument(
        "-o", "--output", nargs="+", default="goa", help="Output prefix. Default: goa"
    )
    return parser

####################################################################
# Main Execution Flow
####################################################################

# Main function to orchestrate the conversion process
def main():
    # Parse command-line arguments
    parser = get_parser()
    args = parser.parse_args()

    # Load version information from the version file
    with open(args.version, "r") as f:
        version = json.load(f)["date"]
    
    # Load the Biolink classes from the YAML config file
    biolinkclasses = yaml_loader(args.cfg)
    # Load the predicate to relation mapping from the RO file
    predicate_to_relation = get_predicate_map(args.ro)
    # Read GO nodes data
    gof = pd.read_csv(args.go, sep="\t")[
        ["id", "category", "name", "provided_by", "xref", "source", "source version"]
    ]
    # Read GAF data
    # This reads GAF files, normalizes data, and maps databases to Biolink categories.
    gaf = read_gaf(args.input, biolinkclasses)
    # Prepare GAF data for node and edge creation
    gaf["provided_by"] = "GOA"
    gaf["id"] = gaf.DB + ":" + gaf["DB Object ID"].str.split("_").str[0]
    gaf["category"] = gaf["Biolink Category"]
    gaf["name"] = gaf["DB Object Symbol"]
    gaf["source"] = "GOA"
    gaf["source version"] = version
    
    # Concatenate GAF data and GO nodes data to create the final nodes DataFrame
    # It merges GAF data and GO nodes into a single DataFrame, preparing the data for node creation.
    nodes = pd.concat(
        [
            gaf[["id", "name", "category", "provided_by", "source", "source version"]],
            gof,
        ]
    )
    # Remove duplicate nodes and save to a file
    # Removes duplicate nodes and saves the resulting DataFrame to a file.
    nodes.drop_duplicates().to_csv(f"{args.output[0]}", sep="\t", index=False)
    
    # Prepare GAF data for edge creation
    # Prepares GAF data for edge creation by setting subject, object, category, and other attributes.
    gaf["object"] = gaf["GO ID"]
    gaf["subject"] = gaf.DB + ":" + gaf["DB Object ID"]
    gaf["category"] = "biolink:FunctionalAssociation"
    # Check if qualifier is negated
    gaf["negated"] = gaf.Qualifier.str.startswith("NOT|")
    # Map qualifier to predicate
    gaf["predicate"] = "biolink:" + gaf.Qualifier.str.replace("NOT|", "", regex=False)
    # Map qualifier to relation
    gaf["relation"] = gaf.Qualifier.map(predicate_to_relation)
    # Set knowledge source
    gaf["knowledge_source"] = "GOA"
    # Select and order the columns for the final edge DataFrame
    gaf = gaf[
    # Selects and orders columns to prepare the edge DataFrame
        [
            "subject",
            "predicate",
            "object",
            "category",
            "negated", 
            "relation",
            "knowledge_source",
            "source",
            "source version",
        ]
    ].drop_duplicates()
    # Add unique edge IDs
    # Generates unique identifiers for each edge.
    gaf["id"] = gaf.subject.apply(lambda x: uuid.uuid4())
    # Save edges to a file
    # Saves the edges to a file.
    gaf.to_csv(f"{args.output[1]}", sep="\t", index=False)

# Script entry point: ensures the main function is called when the script is executed directly.
if __name__ == "__main__":
    main()
