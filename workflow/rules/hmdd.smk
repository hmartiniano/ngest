HMDD_VERSION = "4.0"
HMDD = "http://www.cuilab.cn/static/hmdd3/data/alldata_v4.txt"

rule download_hmdd:
    output: "../data/raw/alldata_v4.txt"
    shell: "curl -L -A 'Mozilla/5.0' {HMDD} -o {output}"

rule process_hmdd:
    input:
        hmdd = "../data/raw/alldata_v4.txt",
        mondo_json = "../data/raw/mondo.json",
        rnamapping = "../data/processed/mappings/rnacentral_tarbase_human_mapping.tsv"
    params:
        version = HMDD_VERSION
    output:
        "../data/processed/finals/hmdd_nodes.tsv",
        "../data/processed/finals/hmdd_edges.tsv"
    shell:
        "python scripts/hmdd_to_kgx.py -i {input.hmdd} -m {input.mondo_json} -r {input.rnamapping} -v '{params.version}' -o {output}"
