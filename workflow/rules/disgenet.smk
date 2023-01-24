DISGENET = "https://www.disgenet.org/static/disgenet_ap1/files/downloads/all_gene_disease_pmid_associations.tsv.gz"
MAPPING = "https://www.disgenet.org/static/disgenet_ap1/files/downloads/disease_mappings.tsv.gz"
DISGENET_VERSION = "https://www.disgenet.org/static/disgenet_ap1/files/downloads/readme.txt"

rule download_disgenet:
  output: "../data/raw/all_gene_disease_pmid_associations.tsv.gz"
  shell: "curl -L {DISGENET} -o {output}"

rule download_disease_mappings:
    output: "../data/raw/disease_mappings.tsv.gz",
    shell: "curl -L {MAPPING} -o {output}"

rule download_disgenet_version:
    output: "../data/raw/disgenet_readme.txt"
    shell: "curl -L {DISGENET_VERSION} -o {output}"

rule process_disgenet:
    input: "../data/raw/all_gene_disease_pmid_associations.tsv.gz", "../data/raw/disease_mappings.tsv.gz", "../data/processed/mappings/ensembl_to_entrez.tsv", version = "../data/raw/disgenet_readme.txt"
    output: "../data/processed/finals/disgenet_nodes.tsv","../data/processed/finals/disgenet_edges.tsv"
    shell: "python scripts/disgenet_to_kgx.py -i {input} -v {input.version}  -o {output}"
