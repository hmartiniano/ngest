MONDO = "purl.obolibrary.org/obo/mondo.json"

rule download_mondo:
  output: "../data/raw/mondo.json"
  shell: "curl -L {MONDO} -o {output}"

rule mondo_mapping:
  input: "../data/raw/mondo.json"
  output: "../data/raw/mondo_mapping.tsv"
  shell: "python scripts/mondo_mapping.py -i {input}  -o {output}"

rule process_mondo:
  input: "../data/raw/mondo.json"
  output: "../data/processed/mondo_nodes.tsv", "../data/processed/mondo_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/mondo -f tsv {input} "
