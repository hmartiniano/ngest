UNIPROT = "https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/HUMAN_9606_idmapping.dat.gz"
UNIPROT_VERSION = "https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/RELEASE.metalink"

rule download_uniprot:
  output: "../data/raw/uniprot.tsv.gz"
  shell: "curl -L {UNIPROT} -o {output}"

rule download_uniprot_version:
  output: "../data/raw/uniprot_release.metalink"
  shell: "curl -L {UNIPROT_VERSION} -o {output}"