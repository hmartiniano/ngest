HPO = "https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/hp.json"

rule download_hpo:
  output: "../data/raw/hpo.json"
  shell: "curl {HPO} -o {output}"

rule process_hpo:
  input: "../data/raw/hpo.json"
  output: "../data/processed/finals/hpo_nodes.tsv", "../data/processed/finals/hpo_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/finals/hpo -f tsv {input} "
