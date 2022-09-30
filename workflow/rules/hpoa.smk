HPOA = "http://purl.obolibrary.org/obo/hp/hpoa/phenotype.hpoa"

rule download_hpoa:
  output: "../data/raw/hpoa.hpoa"
  shell: "curl -L {HPOA} -o {output}"

rule process_hpoa:
  input: "../data/raw/hpoa.hpoa"
  output: "../data/processed/hpoa_nodes.tsv","../data/processed/hpoa_edges.tsv"
  shell: "python scripts/hpoa_to_kgx.py -i {input} -o {output}"
