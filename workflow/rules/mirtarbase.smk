MIRTARBASE_VERSION = "10.0"
MIRTARBASE = "https://awi.cuhk.edu.cn/miRTarBase/downloads/files/10.0/hsa_MTI.csv"

rule download_mirtarbase:
    output: "../data/raw/hsa_MTI.csv"
    shell: "curl --fail --retry 10 --retry-delay 30 --retry-all-errors -k -L {MIRTARBASE} -o {output}"

rule process_mirtarbase:
    input:
        mirtarbase = "../data/raw/hsa_MTI.csv",
        rnamapping = "../data/processed/mappings/rnacentral_tarbase_human_mapping.tsv"
    params:
        version = MIRTARBASE_VERSION
    output:
        "../data/processed/finals/mirtarbase_nodes.tsv",
        "../data/processed/finals/mirtarbase_edges.tsv"
    shell:
        "python scripts/mirtarbase_to_kgx.py -i {input.mirtarbase} -r {input.rnamapping} -v '{params.version}' -o {output}"
