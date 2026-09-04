ENSEMBL_RELEASE = "116"
ENSEMBLPROTEINS = f"https://ftp.ensembl.org/pub/release-{ENSEMBL_RELEASE}/tsv/homo_sapiens/Homo_sapiens.GRCh38.{ENSEMBL_RELEASE}.uniprot.tsv.gz"
ENSEMBLGENES = f"https://ftp.ensembl.org/pub/release-{ENSEMBL_RELEASE}/gtf/homo_sapiens/Homo_sapiens.GRCh38.{ENSEMBL_RELEASE}.gtf.gz"
ENSEMBLENTREZ = f"https://ftp.ensembl.org/pub/release-{ENSEMBL_RELEASE}/tsv/homo_sapiens/Homo_sapiens.GRCh38.{ENSEMBL_RELEASE}.entrez.tsv.gz"

rule download_ensembl:
  output: f"../data/raw/Homo_sapiens.GRCh38.{ENSEMBL_RELEASE}.uniprot.tsv.gz"
  shell: "curl -L {ENSEMBLPROTEINS} -o {output}"

rule download_ensembl_genes:
  output: f"../data/raw/Homo_sapiens.GRCh38.{ENSEMBL_RELEASE}.gtf.gz"
  shell: "curl -L {ENSEMBLGENES}  -o {output}"

rule download_ensembl_entrez_mapping:
  output: f"../data/raw/Homo_sapiens.GRCh38.{ENSEMBL_RELEASE}.entrez.tsv.gz"
  shell: "curl -L {ENSEMBLENTREZ}  -o {output}"


rule process_ensembl_entrez_mapping:
  input: f"../data/raw/Homo_sapiens.GRCh38.{ENSEMBL_RELEASE}.entrez.tsv.gz"
  output: "../data/processed/mappings/ensembl_to_entrez.tsv"
  shell: "python scripts/ensembl_to_entrez.py -i {input} -o {output}"


rule filter_ensembl_genes:
  input: f"../data/raw/Homo_sapiens.GRCh38.{ENSEMBL_RELEASE}.gtf.gz"
  output: "../data/processed/intermediary/ensembl_genes.csv"
  shell: "zcat {input}| awk -F \"\t\" '$3 == \"gene\" {{ print $9 }}' | awk -F \"; \" 'BEGIN {{OFS=\"\t\"}} {{ print > \"{output}\" }}'"


rule process_ensembl:
  input: ensembl = f"../data/raw/Homo_sapiens.GRCh38.{ENSEMBL_RELEASE}.uniprot.tsv.gz", uniprot = "../data/raw/uniprot.tsv.gz", genes = "../data/processed/intermediary/ensembl_genes.csv"
  output: "../data/processed/finals/ensembl_nodes.tsv" , "../data/processed/finals/ensembl_edges.tsv"
  shell: "python scripts/ensembl_to_kgx.py -i {input.ensembl} -u {input.uniprot} -g {input.genes}  -o {output}"

