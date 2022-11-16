#ALL RNA CENTRAL MAPPINGS - 6GB
#RNACENTRAL = "https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/id_mapping/id_mapping.tsv.gz"

#Ensembl Mappings

RNACENTRALENSEMBLMAPPING = "https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/id_mapping/database_mappings/ensembl.tsv"
RNACENTRAL = "https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/gpi/rnacentral.gpi.gz"
RNAVERSION = "https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/release_notes.txt"
RNACENTRALTARBASEMAPPING = "https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/id_mapping/database_mappings/tarbase.tsv"
RNANONCODINGMAPPING = "https://ftp.ebi.ac.uk/pub/databases/RNAcentral/current_release/id_mapping/database_mappings/noncode.tsv"


rule download_rnacentral_ensembl_mapping:
  output: "../data/raw/rnacentralensemblmapping.tsv"
  shell: "curl -L {RNACENTRALENSEMBLMAPPING} -o {output}"


rule download_rnacentral_tarbase_mapping:
  output: "../data/raw/rnacentraltarbasemapping.tsv"
  shell: "curl -L {RNACENTRALTARBASEMAPPING} -o {output}"

rule download_rnacentral_noncoding_mapping:
  output: "../data/raw/rnacentralnoncodingmapping.tsv"
  shell: "curl -L {RNANONCODINGMAPPING} -o {output}"

rule download_rnacentral:
  output: "../data/raw/rnacentral.gpi.gz"
  shell: "curl -L {RNACENTRAL} -o {output}"

rule download_rnacentral_version:
  output: "../data/raw/rnacentral_release_notes.txt"
  shell: "curl -L {RNAVERSION} -o {output}"

rule filter_rnacentral_ensembl_mapping:
  input: "../data/raw/rnacentralensemblmapping.tsv"
  output: "../data/processed/mappings/rnacentral_ensembl_human_mapping.tsv"
  shell: "awk 'BEGIN {{OFS=\"\t\"}} {{ if ($4 == 9606) print $0}}' {input} > {output}"

rule filter_rnacentral_noncode_mapping:
  input: "../data/raw/rnacentralnoncodingmapping.tsv"
  output: "../data/processed/mappings/rnacentral_noncode_human_mapping.tsv"
  shell: "awk 'BEGIN {{OFS=\"\t\"}} {{ if ($4 == 9606) print $0}}' {input} > {output}"

rule filter_rnacentral_tarbase_mapping:
  input: "../data/raw/rnacentraltarbasemapping.tsv"
  output: "../data/processed/mappings/rnacentral_tarbase_human_mapping.tsv"
  shell: "awk 'BEGIN {{OFS=\"\t\"}} {{ if ($4 == 9606) print $0}}' {input} > {output}"

rule filter_rnacentral:
  input:  "../data/raw/rnacentral.gpi.gz"
  output: "../data/processed/intermediary/rnacentral_human.tsv"
  shell: "zcat {input} | awk -F \"\t\"  'BEGIN {{OFS=\"\t\"}} {{ if ($1!~/^!/ && $7 == \"taxon:9606\") print $1,$2,$4,$6}}' > {output}"


rule process_rnacentral:
  input: rnacentral ="../data/processed/intermediary/rnacentral_human.tsv", mapping = "../data/processed/mappings/rnacentral_ensembl_human_mapping.tsv", genes = "../data/processed/intermediary/ensembl_genes.csv"
  output: "../data/processed/finals/rnacentral_nodes.tsv" , "../data/processed/finals/rnacentral_edges.tsv"
  shell: "python scripts/rnacentral_to_kgx.py -i {input.rnacentral} -m {input.mapping} -g {input.genes} -o {output}"










