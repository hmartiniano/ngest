rule download_rnacentral:
  output: "../data/raw/rnacentral.tsv"
  shell: "python scripts/get_rnacentral_data.py -o {output}"


