rule download_uniprot:
  output: "../data/raw/uniprot.tsv"
  shell: "python scripts/get_uniprot_data.py -o {output}"