NPINTER = "http://bigdata.ibp.ac.cn/npinter4/download/file/interaction_NPInterv4.txt.gz"

rule download_npinter:
    output: "../data/raw/interaction_NPInterv4.txt.gz"
    shell: "curl -L {NPINTER} -o {output}"

rule filter_npinter:
  input:  "../data/raw/interaction_NPInterv4.txt.gz"
  output: "../data/processed/intermediary/npinter_human.tsv"
  shell: "zcat {input} | awk -F \"\t\"  'BEGIN {{OFS=\"\t\"}} {{ if ($1 == \"interID\" || $11 == \"Homo sapiens\") print $0}}' > {output}"


rule process_npinter:
    input: npinter = "../data/processed/intermediary/npinter_human.tsv", rnamapping="../data/raw/rnacentralnoncodingmapping.tsv", proteinmapping = "../data/raw/uniprot.tsv.gz", genemapping = "../data/processed/intermediary/ensembl_genes.csv"
    output: "../data/processed/finals/npinter_nodes.tsv", "../data/processed/finals/npinter_edges.tsv"
    shell: "python scripts/npinter_to_kgx.py -i {input.npinter} -r {input.rnamapping} -p {input.proteinmapping} -g {input.genemapping} -o {output}"

