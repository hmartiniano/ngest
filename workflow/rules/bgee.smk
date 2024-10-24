BGEE = "https://bgee.org/ftp/bgee_v15_2/download/calls/expr_calls/Homo_sapiens_expr_simple.tsv.gz"

rule download_bgee:
  output: "../data/raw/bgee_v15_2_Homo_sapiens_expr_simple.tsv.gz"
  shell: "curl -L {BGEE} -o {output}"

rule process_bgee:
  input: "../data/raw/bgee_v15_2_Homo_sapiens_expr_simple.tsv.gz"
  output: "../data/processed/finals/bgee_nodes.tsv" , "../data/processed/finals/bgee_edges.tsv"
  shell: "python scripts/bgee_to_kgx.py -i {input}  -o {output}"
