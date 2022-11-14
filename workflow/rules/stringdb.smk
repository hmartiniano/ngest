STRING = "https://stringdb-static.org/download/protein.links.v11.5/9606.protein.links.v11.5.txt.gz"
rule download_stringdb:
    output: "../data/raw/9606.protein.links.v11.5.txt.gz"
    shell: "curl -L {STRING} -o {output}"

rule process_stringdb:
    input: string = "../data/raw/9606.protein.links.v11.5.txt.gz", proteinmapping = "../data/raw/uniprot.tsv.gz"
    output: "../data/processed/finals/string_nodes.tsv", "../data/processed/finals/string_edges.tsv"
    shell: "python scripts/stringdb_to_kgx.py -i {input.string} -p {input.proteinmapping} -o {output}"

