#CL = "https://github.com/obophenotype/cell-ontology/raw/master/cl.json"
CL = "https://github.com/obophenotype/cell-ontology/releases/download/v2023-02-15/cl-base.json"
PRMAPPING = "https://proconsortium.org/download/current/promapping.txt"

rule download_cl:
  output: "../data/raw/cl.json"
  shell: "curl -L {CL} -o {output}"


rule cl_to_kgx:
  input: "../data/raw/cl.json"
  output: "../data/processed/intermediary/cl_nodes.tsv", "../data/processed/intermediary/cl_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/intermediary/cl -f tsv {input} "

rule download_pr_mapping:
  output: "../data/raw/pr_mapping.txt"
  shell: "curl -L {PRMAPPING} -o {output}"

rule process_cl:
  input: nodes = "../data/processed/intermediary/cl_nodes.tsv", edges = "../data/processed/intermediary/cl_edges.tsv", mapping = "../data/raw/pr_mapping.txt"
  output: "../data/processed/finals/cl_nodes.tsv", "../data/processed/finals/cl_edges.tsv"
  shell: "python scripts/cl_kgx_process.py -i {input.nodes} {input.edges} -m {input.mapping} -o {output}"
