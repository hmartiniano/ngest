BGEE = "https://bgee.org/ftp/bgee_v15_0/download/calls/expr_calls/Homo_sapiens_expr_simple.tsv.gz"

rule download_bgee:
  output: "../data/raw/Homo_sapiens_expr_simple.tsv.gz"
  shell: "curl -L {BGEE} -o {output}"

rule process_bgee:
  input: "../data/raw/Homo_sapiens_expr_simple.tsv.gz"
  output: "../data/processed/bgee_nodes.tsv" , "../data/processed/bgee_edges.tsv"
  shell: "python scripts/bgee_to_kgx.py -i {input}  -o {output}"
