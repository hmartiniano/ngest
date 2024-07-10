STRING_VERSION="12.0"
STRING = f"https://stringdb-downloads.org/download/protein.links.v{STRING_VERSION}/9606.protein.links.v{STRING_VERSION}.txt.gz"
rule download_stringdb:
    output: f"../data/raw/9606.protein.links.v{STRING_VERSION}.txt.gz"
    shell: "curl -L {STRING} -o {output}"

rule process_stringdb:
    input: string = f"../data/raw/9606.protein.links.v{STRING_VERSION}.txt.gz", proteinmapping = "../data/raw/uniprot.tsv.gz"
    output: "../data/processed/finals/string_nodes.tsv", "../data/processed/finals/string_edges.tsv"
    shell: "python scripts/stringdb_to_kgx.py -i {input.string} -p {input.proteinmapping} -o {output}"

