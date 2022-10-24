import yaml
import pandas as pd

class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)

def get_input_files():
    with open("../config/databases_config.yaml") as f:
        databases = pd.DataFrame(yaml.full_load(f)['databases'])
        source = {}
        files = []
        for i in range(len(databases)):
            info = {}
            input = {}
            input["format"] = "tsv"
            input["filename"] = [databases["nodes"][i], databases["edges"][i]]
            info["input"] = input
            source[databases["source"][i]] = info
            files.append(databases["nodes"][i])
            files.append(databases["edges"][i])

    with open("../config/merge_config.yaml") as file:
        mergef = yaml.full_load(file)
        mergef["merged_graph"]["source"] = source

    with open("../config/merge_config.yaml",'w') as f:
        yaml.dump(mergef,f,Dumper=Dumper)
    return (files)