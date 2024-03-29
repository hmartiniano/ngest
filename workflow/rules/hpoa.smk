HPOA = "http://purl.obolibrary.org/obo/hp/hpoa/phenotype.hpoa"

rule download_hpoa:
  output: "../data/raw/hpoa.hpoa"
  shell: "curl -L {HPOA} -o {output}"

rule process_hpoa:
  input: hpoa ="../data/raw/hpoa.hpoa", mondo_map = "../data/raw/mondo_mapping.tsv", hpo = "../data/processed/finals/hpo_nodes.tsv"
  output: "../data/processed/finals/hpoa_nodes.tsv","../data/processed/finals/hpoa_edges.tsv"
  shell: "python scripts/hpoa_to_kgx.py -i {input.hpoa} -m {input.mondo_map} -n {input.hpo} -o {output}"
