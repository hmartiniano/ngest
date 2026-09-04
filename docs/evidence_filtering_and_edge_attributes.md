# Evidence Tracking, Confidence Scoring, and Edge Attribute Harmonization in *ngest*

## 1. Overview

To address biological heterogeneity and enable fine-grained graph filtering for downstream Graph Neural Networks (GNNs) and topological analyses, *ngest* integrates standardized evidence attributes, experimental assay classifications, confidence scores, and literature citations directly onto edges across its constituent databases.

---

## 2. Database Evidence Specifications

### 2.1 DIANA-TarBase (v9.0)
* **Script**: [`workflow/scripts/tarbase_to_kgx.py`](file:///home/hugo/dev/ngest/workflow/scripts/tarbase_to_kgx.py)
* **Ingested Edge Attributes**:
  * `assay_type`: The exact experimental technique recorded in TarBase (e.g. *Luciferase Reporter Assay*, *qPCR*, *Western Blot*, *PAR-CLIP*, *HITS-CLIP*).
  * `validation_type`: High-level categorization into:
    * **`Direct`**: Low-throughput, direct validation assays (*Luciferase Reporter Assay*, *qPCR*, *Western Blot*, *Northern Blot*, *Biotin-qPCR*, *ELISA*, *Immunohistochemistry*, *Immunofluorescence*, *2D-DIGE*).
    * **`High-throughput`**: Omics and sequencing-based assays (*HITS-CLIP*, *PAR-CLIP*, *qCLASH*, *Microarrays*, *RNA-Seq*, *sRNA-Seq*, *Chimeric fragments*, *pSILAC*, *RPF-Seq*).
  * `publications`: Formatted according to the Biolink Model specification as `PMID:<id>` from the primary literature.
  * `has_confidence_level`: Numeric confidence level from TarBase.
  * `relation`: Standardized to `RO:0002434` (*interacts with*).
* **CLI Filtering Options**:
  * `--direct-only`: Retains exclusively direct wet-lab validation assays.
  * `--assay-type`: Accepts a comma-separated list of specific assay methods to retain.

### 2.2 NPInter (v5.0)
* **Script**: [`workflow/scripts/npinter_to_kgx.py`](file:///home/hugo/dev/ngest/workflow/scripts/npinter_to_kgx.py)
* **Data Source**: Confirmed NPInter v5 (`http://bigdata.ibp.ac.cn/npinter5/`).
* **Ingested Edge Attributes**:
  * `assay_type`: Experimental assay recorded in NPInter (e.g. *EMSA*, *CLIP-seq*, *RIP-seq*, *Pull-down*, *Yeast two-hybrid*).
  * `interaction_level`: Categorical interaction level (*RNA-Protein*, *RNA-RNA*, *RNA-DNA*).
  * `publications`: PubMed citations parsed and prefixed as `PMID:<id>` (multiple PMIDs delimited by `|`).
  * `tissue_or_cell`: Tissue or cell line context where the interaction was identified.
  * `relation`: Mapped from interaction class:
    * `biolink:interacts_with` $\rightarrow$ `RO:0002434`
    * `biolink:regulates` $\rightarrow$ `RO:0002448`
    * `biolink:correlated_with` / `biolink:coexpressed_with` $\rightarrow$ `RO:0002610`

### 2.3 STRING DB (v12.5)
* **Script**: [`workflow/scripts/stringdb_to_kgx.py`](file:///home/hugo/dev/ngest/workflow/scripts/stringdb_to_kgx.py)
* **Ingested Edge Attributes**:
  * `has_confidence_level` / `combined_score`: Raw integer combined confidence score ($0 - 1000$).
  * `confidence_score`: Normalized float value on the $[0.0, 1.0]$ scale ($S / 1000.0$) conforming to the Biolink Model confidence representation.
  * `relation`: Standardized to `RO:0002434` (*interacts with*).
* **CLI Filtering Options**:
  * `--min-score`: Minimum integer combined score cutoff (e.g. `--min-score 700` for high-confidence PPIs; defaults to `0` for backward compatibility).

### 2.4 Bgee (v15.0)
* **Script**: [`workflow/scripts/bgee_to_kgx.py`](file:///home/hugo/dev/ngest/workflow/scripts/bgee_to_kgx.py)
* **Ingested Edge Attributes**:
  * `call_quality`: Expression reliability category (*gold quality* vs *silver quality*).
  * `fdr`: False Discovery Rate $p$-value for the gene expression call.
  * `expression_score`: Normalized expression level score.
  * `expression_rank`: Relative expression rank within the anatomical entity.
  * `relation`: Standardized to `RO:0002206` (*expressed in*).
* **CLI Filtering Options**:
  * `--gold-only`: Retains only *gold quality* expression calls.
  * `--max-fdr`: Filters expression calls by maximum FDR (e.g. `--max-fdr 0.01`).

---

## 3. Neo4j Administrative Import Integration

**Script**: [`workflow/scripts/tsv_to_neo4j.py`](file:///home/hugo/dev/ngest/workflow/scripts/tsv_to_neo4j.py)

The Neo4j conversion engine automatically maps edge attributes to strongly-typed Neo4j CSV import headers:
* `predicate:TYPE`
* `subject:START_ID`
* `object:END_ID`
* `confidence_score:float`
* `has_confidence_level:float`
* `combined_score:int`
* `fdr:float`
* `expression_score:float`
* `expression_rank:float`
* `publications:string[]` (semicolon-delimited list for Cypher array operations)
* `assay_type:string`
* `validation_type:string`
* `call_quality:string`
* `interaction_level:string`

This typing ensures that Neo4j users can perform numeric and array filtering directly in Cypher without runtime casting:
```cypher
MATCH (rna:RNAProduct)-[e:interacts_with]->(g:Gene)
WHERE e.validation_type = 'Direct'
  AND 'PMID:20371350' IN e.publications
RETURN rna.name, g.name, e.assay_type;
```

---

## 4. Sample Cypher Queries

A collection of publication-ready Cypher queries demonstrating multi-hop disease traversal, high-confidence PPI subgraphs, and direct ncRNA regulatory cascades is available in:
[`workflow/notebooks/sample_queries.cypher`](file:///home/hugo/dev/ngest/workflow/notebooks/sample_queries.cypher).
