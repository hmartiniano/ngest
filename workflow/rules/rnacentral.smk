#rule download_rnacentral:
#  output: "../data/raw/rnacentral.tsv"
#  shell: "python scripts/get_rnacentral_data_old.py -o {output}"


#ALL RNA CENTRAL MAPPINGS - 6GB
#RNACENTRAL = "https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/id_mapping/id_mapping.tsv.gz"

#Ensembl Mappings

RNACENTRAL = "https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/id_mapping/database_mappings/ensembl.tsv"
RNAVERSION = "https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/release_notes.txt"

rule download_rnacentral:
  output: "../data/raw/rnacentral.tsv"
  shell: "curl -L {RNACENTRAL} -o {output}"

rule download_rnacentral_version:
  output: "../data/raw/rnacentral_release_notes.txt"
  shell: "curl -L {RNAVERSION} -o {output}"

rule filter_rnacentral:
  input: "../data/raw/rnacentral.tsv"
  output: "../data/processed/rnacentral.tsv"
  shell: "awk '$4 = 9606 {{print $0}}' {input} > {output}"







