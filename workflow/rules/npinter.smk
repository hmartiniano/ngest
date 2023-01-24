NPINTER = "http://bigdata.ibp.ac.cn/npinter5/download/file/interaction_NPInterv5.txt.gz"

rule download_npinter:
    output: "../data/raw/interaction_NPInterv5.txt.gz"
    shell: "curl -L {NPINTER} -o {output}"

rule filter_npinter:
  input:  "../data/raw/interaction_NPInterv5.txt.gz"
  output: "../data/processed/intermediary/interaction_NPInterv5_human.tsv"
  shell: "zcat {input} | awk -F \"\t\"  'BEGIN {{OFS=\"\t\"}} {{ if ($1 == \"interID\" || $11 == \"Homo sapiens\") print $0}}' > {output}"

rule process_npinter:
    input: npinter = "../data/processed/intermediary/interaction_NPInterv5_human.tsv", noncoddingmapping="../data/processed/mappings/rnacentral_noncode_human_mapping.tsv", tarbasemapping= "../data/processed/mappings/rnacentral_tarbase_human_mapping.tsv", ensemblmapping = "../data/processed/mappings/rnacentral_ensembl_human_mapping.tsv", proteinmapping = "../data/raw/uniprot.tsv.gz", genemapping = "../data/processed/intermediary/ensembl_genes.csv"
    output: "../data/processed/finals/npinter_nodes.tsv", "../data/processed/finals/npinter_edges.tsv"
    shell: "python scripts/npinter_to_kgx.py -i {input.npinter} -r {input.noncoddingmapping} {input.tarbasemapping} {input.ensemblmapping} -p {input.proteinmapping} -g {input.genemapping} -o {output}"

