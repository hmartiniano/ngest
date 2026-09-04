LNCBOOK_VERSION = "2.0"
LNCBOOK = "https://ngdc.cncb.ac.cn/lncbook/files/lncrna_mirna_miRandaAndTargetScanAndRNAhybrid_LncBook2.0.csv.gz"

rule download_lncbook:
    output: "../data/raw/lncrna_mirna_LncBook2.0.csv.gz"
    shell: "curl -L -A 'Mozilla/5.0' {LNCBOOK} -o {output}"

rule process_lncbook:
    input:
        lncbook = "../data/raw/lncrna_mirna_LncBook2.0.csv.gz",
        rnamapping = "../data/processed/mappings/rnacentral_tarbase_human_mapping.tsv"
    params:
        version = LNCBOOK_VERSION
    output:
        "../data/processed/finals/lncbook_nodes.tsv",
        "../data/processed/finals/lncbook_edges.tsv"
    shell:
        "python scripts/lncbook_to_kgx.py -i {input.lncbook} -r {input.rnamapping} -v '{params.version}' -o {output}"
