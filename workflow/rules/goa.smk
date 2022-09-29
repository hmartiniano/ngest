GOAP = "http://geneontology.org/gene-associations/goa_human.gaf.gz"
GOAC = "http://geneontology.org/gene-associations/goa_human_complex.gaf.gz"
GOAR = "http://geneontology.org/gene-associations/goa_human_rna.gaf.gz"
# GOAI = "http://geneontology.org/gene-associations/goa_human_isoform.gaf.gz"

rule download_goa_proteins:
  output: "../data/raw/goa_Protein.gaf"
  shell: "wget -qO- {GOAP}  | gzip  -d > {output}"

rule download_goa_complex:
  output: "../data/raw/goa_MacromolecularComplexMixin.gaf" #confirmar o nome
  shell: "wget -qO- {GOAC}  | gzip  -d > {output}"

rule download_goa_rna:
  output: "../data/raw/goa_Transcript.gaf"
  shell: "wget -qO- {GOAR}  | gzip  -d > {output}"

# rule download_goa_isoform:
#   output: "../data/raw/goa_ProteinIsoform.gaf"
#   shell: "wget -c {GOAI} -O {output}"


rule process_goa:
  input: "../data/raw/goa_Protein.gaf","../data/raw/goa_MacromolecularComplexMixin.gaf","../data/raw/goa_Transcript.gaf" #, "../data/raw/goa_proteins.gaf"
  params: "../data/raw/ro.json"
  output: "../data/processed/goa_nodes.tsv","../data/processed/goa_edges.tsv"
  shell: "python scripts/goa_to_kgx.py -i {input} -r {params} -o {output}"
