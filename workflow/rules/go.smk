GO = "http://current.geneontology.org/ontology/go.json"

rule download_go:
  output: "../data/raw/go.json"
  shell: "curl {GO} -o {output}"

rule process_go:
  input: "../data/raw/go.json", "../data/raw/ro.json"
  output: "../data/processed/go_nodes.tsv", "../data/processed/go_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/go -f tsv {input} "
