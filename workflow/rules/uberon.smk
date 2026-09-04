UBERON_VERSION = "v2026-06-23"
UBERON = "http://purl.obolibrary.org/obo/uberon/subsets/human-view.json"

rule download_uberon:
  output: "../data/raw/uberon.json"
  shell: "curl -L {UBERON} -o {output}"


rule process_uberon:
  input: "../data/raw/uberon.json"
  output: "../data/processed/intermediary/uberon_nodes.tsv", "../data/processed/intermediary/uberon_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/intermediary/uberon -f tsv {input}"

rule add_uberon_version:
  input: "../data/processed/intermediary/uberon_nodes.tsv","../data/processed/intermediary/uberon_edges.tsv"
  params: version = UBERON_VERSION
  output: "../data/processed/finals/uberon_nodes.tsv","../data/processed/finals/uberon_edges.tsv"
  shell: "python scripts/uberon_kgx_process.py -i {input} -v '{params.version}' -o {output}"