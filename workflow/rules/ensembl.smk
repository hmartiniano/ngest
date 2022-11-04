ENSEMBLPROTEINS = "https://ftp.ensembl.org/pub/current_tsv/homo_sapiens/Homo_sapiens.GRCh38.108.uniprot.tsv.gz"
ENSEMBLGENES = "https://ftp.ensembl.org/pub/current_gtf/homo_sapiens/Homo_sapiens.GRCh38.108.gtf.gz"
ENSEMBLENTREZ = "https://ftp.ensembl.org/pub/current_tsv/homo_sapiens/Homo_sapiens.GRCh38.108.entrez.tsv.gz"

rule download_ensembl:
  output: "../data/raw/Homo_sapiens.GRCh38.108.uniprot.tsv.gz"
  shell: "curl -L {ENSEMBLPROTEINS} -o {output}"

rule download_ensembl_genes:
  output: "../data/raw/Homo_sapiens.GRCh38.108.gtf.gz"
  shell: "curl -L {ENSEMBLGENES}  -o {output}"

rule download_ensembl_entrez_mapping:
  output: "../data/raw/Homo_sapiens.GRCh38.108.entrez.tsv.gz"
  shell: "curl -L {ENSEMBLENTREZ}  -o {output}"


rule process_ensembl_entrez_mapping:
  input: "../data/raw/Homo_sapiens.GRCh38.108.entrez.tsv.gz"
  output: "../data/processed/mappings/ensembl_to_entrez.tsv"
  shell: "python scripts/ensembl_to_entrez.py -i {input} -o {output}"


rule filter_ensembl_genes:
  input: "../data/raw/Homo_sapiens.GRCh38.108.gtf.gz"
  output: "../data/processed/intermediary/ensembl_genes.csv"
  shell: "zcat {input}| awk -F \"\t\" '$3 == \"gene\" {{ print $9 }}' | awk -F \"; \" 'BEGIN {{OFS=\"\t\"}} {{ print > \"{output}\" }}'"


rule process_ensembl:
  input: ensembl = "../data/raw/Homo_sapiens.GRCh38.108.uniprot.tsv.gz" , uniprot = "../data/raw/uniprot.tsv.gz", genes = "../data/processed/intermediary/ensembl_genes.csv"
  output: "../data/processed/finals/ensembl_nodes.tsv" , "../data/processed/finals/ensembl_edges.tsv"
  shell: "python scripts/ensembl_to_kgx.py -i {input.ensembl} -u {input.uniprot} -g {input.genes}  -o {output}"

