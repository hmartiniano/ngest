MONDO_VERSION = "v2026-08-04"
MONDO = "http://purl.obolibrary.org/obo/mondo.json"

rule download_mondo:
  output: "../data/raw/mondo.json"
  shell: "curl -L {MONDO} -o {output}"

rule mondo_mapping:
  input: "../data/raw/mondo.json"
  output: "../data/raw/mondo_mapping.tsv"
  shell: "python scripts/mondo_mapping.py -i {input}  -o {output}"

rule process_mondo:
  input: "../data/raw/mondo.json"
  output: "../data/processed/intermediary/mondo_nodes.tsv", "../data/processed/intermediary/mondo_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/intermediary/mondo -f tsv {input} "

rule add_mondo_version:
  input: "../data/processed/intermediary/mondo_nodes.tsv","../data/processed/intermediary/mondo_edges.tsv"
  params: version = MONDO_VERSION
  output: "../data/processed/finals/mondo_nodes.tsv","../data/processed/finals/mondo_edges.tsv"
  shell: "python scripts/mondo_kgx_process.py -i {input} -v '{params.version}' -o {output}"
