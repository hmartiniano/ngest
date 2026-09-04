RNADISEASE_VERSION = "4.0"
RNADISEASE_URL = "http://www.rnadisease.org/static/download/RNADiseasev4.0_RNA-disease_experiment_all.zip"

rule download_rnadisease:
    output:
        zip = "../data/raw/rnadisease_v4.zip",
        xlsx = "../data/raw/RNADiseasev4.0_RNA-disease_experiment_all.xlsx",
        tsv = "../data/raw/rnadisease_v4.tsv.gz"
    params:
        url = RNADISEASE_URL
    shell:
        """
        curl -fSL -A 'Mozilla/5.0' -e 'http://www.rnadisease.org/download' '{params.url}' -o {output.zip}
        unzip -q -o {output.zip} -d ../data/raw/
        python -c "import openpyxl, csv, gzip; wb = openpyxl.load_workbook('{output.xlsx}', read_only=True); ws = wb.active; f = gzip.open('{output.tsv}', 'wt', encoding='utf-8', newline=''); w = csv.writer(f, delimiter='\\t', lineterminator='\\n'); [w.writerow(['' if c is None else str(c).strip() for c in r]) for r in ws.iter_rows(values_only=True)]; f.close()"
        """

rule process_rnadisease:
    input:
        rnadisease = "../data/raw/rnadisease_v4.tsv.gz",
        mondo_json = "../data/raw/mondo.json",
        rnamapping = "../data/processed/mappings/rnacentral_tarbase_human_mapping.tsv",
        ensembl_mapping = "../data/processed/mappings/rnacentral_ensembl_human_mapping.tsv",
        noncode_mapping = "../data/processed/mappings/rnacentral_noncode_human_mapping.tsv",
        genes = "../data/processed/intermediary/ensembl_genes.csv"
    params:
        version = RNADISEASE_VERSION
    output:
        "../data/processed/finals/rnadisease_nodes.tsv",
        "../data/processed/finals/rnadisease_edges.tsv"
    shell:
        "python scripts/rnadisease_to_kgx.py -i {input.rnadisease} -m {input.mondo_json} -r {input.rnamapping} -e {input.ensembl_mapping} -n {input.noncode_mapping} -g {input.genes} -v '{params.version}' -o {output}"
