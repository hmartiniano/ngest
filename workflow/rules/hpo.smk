HPO = "https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/hp.json"

rule download_hpo:
  output: "../data/raw/hpo.json"
  shell: "curl {HPO} -o {output}"

rule process_hpo:
  input: "../data/raw/hpo.json"
  output: "../data/processed/hpo_nodes.tsv", "../data/processed/hpo_edges.tsv"
  shell: "kgx transform -i obojson -o ../data/processed/hpo -f tsv {input} "
