GOAP = "http://geneontology.org/gene-associations/goa_human.gaf.gz"
GOAC = "http://geneontology.org/gene-associations/goa_human_complex.gaf.gz"
GOAR = "http://geneontology.org/gene-associations/goa_human_rna.gaf.gz"
GOAI = "http://geneontology.org/gene-associations/goa_human_isoform.gaf.gz"
GOAVERSION = "http://current.geneontology.org/metadata/release-date.json"

rule download_goa_proteins:
  output: "../data/raw/goa_human.gaf.gz"
  shell: "curl -L {GOAP} -o {output}"

rule download_goa_complex:
  output: "../data/raw/goa_human_complex.gaf.gz" #confirmar o nome
  shell: "curl -L {GOAC} -o {output}"

rule download_goa_rna:
  output: "../data/raw/goa_human_rna.gaf.gz"
  shell: "curl -L {GOAR} -o {output}"

rule download_goa_isoform:
  output: "../data/raw/goa_human_isoform.gaf.gz"
  shell: "curl -L {GOAI} -o {output}"

rule download_goa_version:
  output: "../data/raw/goa_release-date.json"
  shell: "curl -L {GOAVERSION} -o {output}"

rule process_goa:
  input: ro="../data/raw/ro.json", cfg= "../config/config.yaml", protein="../data/raw/goa_human.gaf.gz", rna="../data/raw/goa_human_rna.gaf.gz", complex="../data/raw/goa_human_complex.gaf.gz"  , isoform = "../data/raw/goa_human_isoform.gaf.gz"
  output: "../data/processed/finals/goa_nodes.tsv","../data/processed/finals/goa_edges.tsv"
  shell: "python scripts/goa_to_kgx.py -i {input.rna} {input.protein} {input.complex} {input.isoform} -r {input.ro}  -c {input.cfg} -o {output}"
