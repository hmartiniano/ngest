#ENSEMBL = "http://ftp.ensembl.org/pub/current_json/homo_sapiens/homo_sapiens.json"

#rule download_ensembl:
#  output: "../data/raw/ensembl.json"
#  shell: "curl {ENSEMBL} -o {output}"

rule download_ensembl:
  output: "../data/raw/ensembl.tsv"
  shell: "python scripts/get_ensembl_data.py -o {output}"

rule download_ensembl_to_entrez_mapping:
  output: "../data/raw/ensembl_to_entrez.tsv"
  shell: "python scripts/ensembl_to_entrez.py -o {output}"

rule process_ensembl:
  input: "../data/raw/ensembl.tsv" , "../data/raw/uniprot.tsv.gz", "../data/processed/rnacentral.tsv"
  output: "../data/processed/ensembl_nodes.tsv" , "../data/processed/ensembl_edges.tsv"
  shell: "python scripts/ensembl_to_kgx.py -i {input}  -o {output}"

