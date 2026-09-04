TARBASE_VERSION = "9.0"
TARBASE = "https://dianalab.e-ce.uth.gr/tarbasev9/data/Homo_sapiens_TarBase-v9.tsv.gz"

rule download_tarbase:
    output: "../data/raw/Homo_sapiens_TarBase-v9.tsv.gz"
    shell: "curl -L {TARBASE} -o {output}"


rule process_tarbase:
    input:
        tarbase = "../data/raw/Homo_sapiens_TarBase-v9.tsv.gz",
        rnamapping = "../data/processed/mappings/rnacentral_tarbase_human_mapping.tsv",
        entrez_mapping = "../data/processed/mappings/ensembl_to_entrez.tsv"
    params:
        version = TARBASE_VERSION
    output:
        "../data/processed/finals/tarbase_nodes.tsv",
        "../data/processed/finals/tarbase_edges.tsv"
    shell:
        "python scripts/tarbase_to_kgx.py -i {input.tarbase} -r {input.rnamapping} -e {input.entrez_mapping} -v '{params.version}' -o {output}"
