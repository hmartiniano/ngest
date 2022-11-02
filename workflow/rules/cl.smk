CL = "https://github.com/obophenotype/cell-ontology/raw/master/cl.json"
PRMAPPING = "https://proconsortium.org/download/current/promapping.txt"

rule download_cl:
  output: "../data/raw/cl.json"
  shell: "curl -L {CL} -o {output}"


rule cl_to_kgx:
  input: "../data/raw/cl.json"
  output: "../data/raw/cl_nodes.tsv", "../data/raw/cl_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/raw/cl -f tsv {input} "

rule download_pr_mapping:
  output: "../data/raw/pr_mapping.txt"
  shell: "curl -L {PRMAPPING} -o {output}"

rule process_cl:
  input: nodes = "../data/raw/cl_nodes.tsv", edges = "../data/raw/cl_edges.tsv", mapping = "../data/raw/pr_mapping.txt"
  output: "../data/processed/cl_nodes.tsv", "../data/processed/cl_edges.tsv"
  shell: "python scripts/cl_kgx_process.py -i {input.nodes} {input.edges} -m {input.mapping} -o {output}"