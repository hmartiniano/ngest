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
  output: "../data/processed/intermediary/go_nodes.tsv", "../data/processed/intermediary/go_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/intermediary/go -f tsv {input} "

rule add_go_version:
  input: "../data/processed/intermediary/go_nodes.tsv","../data/processed/intermediary/go_edges.tsv", version = "../data/raw/go_release-date.json"
  output: "../data/processed/finals/go_nodes.tsv","../data/processed/finals/go_edges.tsv"
  shell: "python scripts/go_kgx_process.py -i {input} -v {input.version} -o {output}"