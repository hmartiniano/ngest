UBERON = "http://purl.obolibrary.org/obo/uberon/subsets/human-view.json"

rule download_uberon:
  output: "../data/raw/uberon.json"
  shell: "curl -L {UBERON} -o {output}"


rule process_uberon:
  input: "../data/raw/uberon.json"
  output: "../data/processed/finals/uberon_nodes.tsv", "../data/processed/finals/uberon_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/finals/uberon -f tsv {input} "