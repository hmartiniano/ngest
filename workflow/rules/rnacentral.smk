#rule download_rnacentral:
#  output: "../data/raw/rnacentral.tsv"
#  shell: "python scripts/get_rnacentral_data_old.py -o {output}"


#ALL RNA CENTRAL MAPPINGS - 6GB
#RNACENTRAL = "https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/id_mapping/id_mapping.tsv.gz"

#Ensembl Mappings
RNACENTRAL = "https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/id_mapping/database_mappings/ensembl.tsv"

rule download_rnacentral:
  output: "../data/raw/rnacentral.tsv"
  params: "{print $0}"
  shell: "wget -qO- {RNACENTRAL}  | awk '$4 = 9606 {params}' > {output}"





