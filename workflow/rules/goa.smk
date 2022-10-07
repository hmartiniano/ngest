GOAP = "http://geneontology.org/gene-associations/goa_human.gaf.gz"
GOAC = "http://geneontology.org/gene-associations/goa_human_complex.gaf.gz"
GOAR = "http://geneontology.org/gene-associations/goa_human_rna.gaf.gz"
#GOAI = "http://geneontology.org/gene-associations/goa_human_isoform.gaf.gz"

rule download_goa_proteins:
  output: "../data/raw/goa_human.gaf.gz"
  shell: "curl -L {GOAP} -o {output}"

rule download_goa_complex:
  output: "../data/raw/goa_human_complex.gaf.gz" #confirmar o nome
  shell: "curl -L {GOAC} -o {output}"

rule download_goa_rna:
  output: "../data/raw/goa_human_rna.gaf.gz"
  shell: "curl -L {GOAR} -o {output}"

#rule download_goa_isoform:
#   output: "../data/raw/goa_human_isoform.gaf.gz"
#   shell: "curl -L {GOAI} -o {output}"


rule process_goa:
  input: ro="../data/raw/ro.json", cfg= "../config/config.yaml", protein="../data/raw/goa_human.gaf.gz", rna="../data/raw/goa_human_complex.gaf.gz", complex="../data/raw/goa_human_rna.gaf.gz"  #, "../data/raw/goa_human_isoform.gaf.gz"
  output: "../data/processed/goa_nodes.tsv","../data/processed/goa_edges.tsv"
  shell: "python scripts/goa_to_kgx.py -i {input.protein} {input.rna} -r {input.ro}  -c {input.cfg} -o {output}"
