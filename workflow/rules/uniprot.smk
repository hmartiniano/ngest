UNIPROT = "https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/HUMAN_9606_idmapping.dat.gz"


rule download_uniprot:
  output: "../data/raw/uniprot.tsv"
  shell: "wget -qO- {UNIPROT}  | gzip  -d > {output}"
