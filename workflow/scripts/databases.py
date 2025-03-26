# This script reads database and merge configurations and returns a list of input files.

import yaml
import pandas as pd

# Define a custom YAML dumper to increase indentation
class Dumper(yaml.Dumper):
    # Override the increase_indent method to control indentation
    def increase_indent(self, flow=False, *args, **kwargs):
        # Call the superclass method with indentless=False to enforce indentation
        return super().increase_indent(flow=flow, indentless=False)


def get_input_files():
    # Open the databases configuration file in read mode
    with open("../config/databases_config.yaml") as f:
        # Load the YAML content and convert it to a Pandas DataFrame
        databases = pd.DataFrame(yaml.full_load(f)["databases"])
        # Initialize an empty dictionary to store source information
        source = {}
        # Initialize an empty list to store file names
        files = []
        # Iterate through each row of the DataFrame
        for i in range(len(databases)):
            # Initialize an empty dictionary for each database's info
            info = {}
            # Initialize an empty dictionary for input specifications
            input = {}
            # Set the default format to "tsv"
            input["format"] = "tsv"
            # Assign the database name
            input["name"] = databases["name"][i]
            # Assign the node and edge filenames
            input["filename"] = [databases["nodes"][i], databases["edges"][i]]
            # Add filters if present
            if databases["filters"][i]:
                input["filters"] = databases["filters"][i]
            # Assign the input specifications to the info
            info["input"] = input
            # Add the info to the source dictionary, using the source name as the key
            source[databases["source"][i]] = info
            # Add the node and edge filenames to the files list
            files.append(databases["nodes"][i])
            files.append(databases["edges"][i])
    # Open the merge configuration file in read mode
    with open("../config/merge_config.yaml") as file:
        # Load the YAML content
        mergef = yaml.full_load(file)
        # Add the source information to the merge config
        mergef["merged_graph"]["source"] = source
    # Open the merge configuration file in write mode
    with open("../config/merge_config.yaml", "w") as f:
        # Dump the modified merge config to the file, using the custom Dumper
        yaml.dump(mergef, f, Dumper=Dumper)
    # Return the list of filenames
    return files
