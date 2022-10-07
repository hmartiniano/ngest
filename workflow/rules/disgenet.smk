DISGENET = "https://www.disgenet.org/static/disgenet_ap1/files/downloads/all_gene_disease_pmid_associations.tsv.gz"
MAPPING = "https://www.disgenet.org/static/disgenet_ap1/files/downloads/disease_mappings.tsv.gz"

rule download_disgenet:
  output: "../data/raw/all_gene_disease_pmid_associations.tsv.gz"
  shell: "curl -L {DISGENET} -o {output}"

rule download_disease_mappings:
    output: "../data/raw/disease_mappings.tsv.gz"
    shell: "curl -L {MAPPING} -o {output}"

rule process_disgenet:
    input: "../data/raw/all_gene_disease_pmid_associations.tsv.gz", "../data/raw/disease_mappings.tsv.gz", "../data/raw/ensembl_to_entrez.tsv"
    output: "../data/processed/disgenet_nodes.tsv","../data/processed/disgenet_edges.tsv"
    shell: "python scripts/disgenet_to_kgx.py -i {input}  -o {output}"