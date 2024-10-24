MIRTARBASE = "https://awi.cuhk.edu.cn/~miRTarBase/miRTarBase_2025/cache/download/10.0/hsa_MTI.csv"

rule download_mirtarbase:
    output: "../data/raw/hsa_MTI.csv"
    shell: "curl -L {MIRTARBASE} -o {output}"


rule mirtarbase_to_csv:
    input: "../data/raw/9.0_hsa_MTI.xlsx"
    output: "../data/processed/intermediary/9.0_hsa_MTI.tsv"
    shell: "python scripts/mirtarbase_to_csv.py -i {input} -o {output}"


rule process_mirtarbase:
    input: mirtarbase="../data/raw/hsa_MTI.csv", rnamapping="../data/processed/mappings/rnacentral_tarbase_human_mapping.tsv", genemapping="../data/processed/mappings/ensembl_to_entrez.tsv", version="10.0"
    output: "../data/processed/finals/mirtarbase_nodes.tsv", "../data/processed/finals/mirtarbase_edges.tsv"
    shell: "python scripts/mirtarbase_to_kgx.py -i {input.mirtarbase} -r {input.rnamapping} -g {input.genemapping} -o {output}"

