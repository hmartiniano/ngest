DISGENET = "https://www.disgenet.org/static/disgenet_ap1/files/downloads/all_gene_disease_pmid_associations.tsv.gz"
MAPPING = "https://www.disgenet.org/static/disgenet_ap1/files/downloads/disease_mappings.tsv.gz"

rule download_disgenet:
  output: "../data/raw/disgenet.tsv"
  shell: "wget -qO- {DISGENET}  | gzip  -d > {output}"

rule download_disease_mappings:
    output: "../data/raw/disease_mappings.tsv"
    shell: "wget -qO- {MAPPING}  | gzip  -d > {output}"

rule process_disgenet:
    input: "../data/raw/disgenet.tsv", "../data/raw/disease_mappings.tsv", "../data/raw/ensembl_to_entrez.tsv"
    output: "../data/processed/disgenet_nodes.tsv","../data/processed/disgenet_edges.tsv"
    shell: "python scripts/disgenet_to_kgx.py -i {input}  -o {output}"