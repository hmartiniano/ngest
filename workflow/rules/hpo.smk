HPO_VERSION = "v2026-06-23"
HPO = "http://purl.obolibrary.org/obo/hp.json"

rule download_hpo:
  output: "../data/raw/hpo.json"
  shell: "curl -L {HPO} -o {output}"

rule process_hpo:
  input: "../data/raw/hpo.json"
  output: "../data/processed/intermediary/hpo_nodes.tsv", "../data/processed/intermediary/hpo_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/intermediary/hpo -f tsv {input} "

rule add_hpo_version:
  input: "../data/processed/intermediary/hpo_nodes.tsv","../data/processed/intermediary/hpo_edges.tsv"
  params: version = HPO_VERSION
  output: "../data/processed/finals/hpo_nodes.tsv","../data/processed/finals/hpo_edges.tsv"
  shell: "python scripts/hpo_kgx_process.py -i {input} -v '{params.version}' -o {output}"