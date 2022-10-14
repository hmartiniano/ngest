CL = "https://github.com/obophenotype/cell-ontology/raw/master/cl.json"

rule download_cl:
  output: "../data/raw/cl.json"
  shell: "curl -L {CL} -o {output}"


rule process_cl:
  input: "../data/raw/cl.json"
  output: "../data/processed/cl_nodes.tsv", "../data/processed/cl_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/cl -f tsv {input} "