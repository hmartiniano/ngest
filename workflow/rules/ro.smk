RO = "http://purl.obolibrary.org/obo/ro.json"

rule download_ro:
  output: "../data/raw/ro.json"
  shell: "curl -L {RO} -o {output}"