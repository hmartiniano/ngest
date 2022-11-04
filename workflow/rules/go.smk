GO = "http://current.geneontology.org/ontology/go.json"
GOVERSION = "http://current.geneontology.org/metadata/release-date.json"

rule download_go:
  output: "../data/raw/go.json"
  shell: "curl {GO} -o {output}"

rule download_go_version:
  output: "../data/raw/go_release-date.json"
  shell: "curl -L {GOVERSION} -o {output}"

rule process_go:
  input: "../data/raw/go.json"
  output: "../data/processed/finals/go_nodes.tsv", "../data/processed/finals/go_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/finals/go -f tsv {input} "
