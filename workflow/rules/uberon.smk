UBERON = "http://purl.obolibrary.org/obo/uberon/subsets/human-view.json"

rule download_uberon:
  output: "../data/raw/uberon.json"
  shell: "curl -L {UBERON} -o {output}"


rule process_uberon:
  input: "../data/raw/uberon.json"
  output: "../data/processed/uberon_nodes.tsv", "../data/processed/uberon_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/uberon -f tsv {input} "