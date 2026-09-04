# Semantic Data Model & Biolink Model Alignment

This document describes the semantic data model used in `ngest`, its alignment with the [Biolink Model](https://biolink.github.io/biolink-model/) (v4.x), the handling of ontology property axioms (`owl:inverseOf`, `rdfs:subPropertyOf`), and the biological rationale behind interaction and association predicates.

---

## 1. Overview of Data Sources & Entity Types

The `ngest` knowledge graph integrates 17 biological databases and ontologies into a unified property graph:

| Source | Role / Type | Primary Node Categories | Primary Predicates / Relations |
| :--- | :--- | :--- | :--- |
| **Ensembl** | Gene/Protein definitions & hierarchy | `biolink:Gene`, `biolink:Protein` | `biolink:has_gene_product` |
| **RNACentral** | Non-coding RNA definitions | `biolink:Gene`, `biolink:RNAProduct` | `biolink:has_gene_product` |
| **STRING DB** | Protein-protein functional associations | `biolink:Protein` | `biolink:interacts_with` (`RO:0002434`) |
| **DIANA-TarBase** | Validated miRNA–target interactions | `biolink:RNAProduct`, `biolink:Gene` | `biolink:interacts_with` (`RO:0002434`) |
| **NPInter** | Non-coding RNA functional interactions | `biolink:RNAProduct`, `biolink:Gene`, `biolink:Protein` | `biolink:interacts_with`, `biolink:regulates`, `biolink:correlated_with`, `biolink:coexpressed_with` |
| **Bgee** | Gene expression in tissues & cells | `biolink:Gene`, `biolink:AnatomicalEntity`, `biolink:Cell` | `biolink:expressed_in` |
| **Gene Ontology (GO)** | Biological process, component, activity | `biolink:BiologicalProcess`, `biolink:CellularComponent`, `biolink:MolecularActivity` | `biolink:subclass_of`, `biolink:related_to`, `owl:inverseOf`, `rdfs:subPropertyOf` |
| **GOA** | Gene Ontology Annotations | `biolink:Protein`, `biolink:RNAProduct`, `biolink:MacromolecularComplex`, GO terms | `biolink:actively_involved_in`, `biolink:enables`, `biolink:part_of`, `biolink:active_in`, `biolink:colocalizes_with` |
| **Cell Ontology (CL)** | Cell type hierarchy | `biolink:Cell`, `biolink:AnatomicalEntity`, `biolink:Protein` | `biolink:subclass_of`, `biolink:related_to`, `owl:inverseOf`, `rdfs:subPropertyOf` |
| **Uberon** | Anatomical structures | `biolink:AnatomicalEntity`, `biolink:Cell` | `biolink:subclass_of`, `biolink:related_to`, `owl:inverseOf`, `rdfs:subPropertyOf` |
| **MONDO** | Disease ontology | `biolink:Disease`, `biolink:PhenotypicFeature` | `biolink:subclass_of`, `biolink:related_to`, `biolink:type`, `owl:inverseOf`, `rdfs:subPropertyOf` |
| **HPO** | Human Phenotype Ontology | `biolink:PhenotypicFeature` | `biolink:subclass_of` |
| **HPOA** | Disease–Phenotype associations | `biolink:Disease`, `biolink:PhenotypicFeature` | `biolink:has_phenotype` |
| **DisGeNET** | Gene–Disease associations | `biolink:Gene`, `biolink:Disease`, `biolink:PhenotypicFeature` | `biolink:associated_with` |
| **HMDD** | Human microRNA–Disease associations (v4.0) | `biolink:RNAProduct`, `biolink:Disease` | `biolink:associated_with` |
| **LncBook** | Consensus lncRNA–miRNA interactions (v2.0) | `biolink:RNAProduct` | `biolink:interacts_with` |
| **miRTarBase** | Experimentally validated miRNA–target interactions (10.0) | `biolink:RNAProduct`, `biolink:Gene` | `biolink:interacts_with` |
| **RNADisease** | Experimentally supported RNA–Disease associations (v4.0) | `biolink:RNAProduct`, `biolink:Disease` | `biolink:associated_with` |

---

## 2. Ontology Axioms: `owl:inverseOf` and `rdfs:subPropertyOf`

### A. Root Cause Analysis
Upstream ontologies (`CL`, `GO`, `MONDO`, `Uberon`) are ingested in **OBO Graph JSON** format (produced via ROBOT / OWLAPI). These files define property relationships (axioms between object properties/relations), such as:
* `BFO:0000050` (*part of*) is the inverse of `BFO:0000051` (*has part*).
* `RO:0002007` (*bounding layer of*) is a subproperty of `BFO:0000050` (*part of*).

In OBO Graph JSON, these are serialized as bare non-IRI strings: `"pred": "inverseOf"` and `"pred": "subPropertyOf"`.

When `kgx transform -i obojson` parses these edges in `kgx/source/obograph_source.py`:
1. It hardcodes mappings for `is_a` $\rightarrow$ `biolink:subclass_of`, `part_of` $\rightarrow$ `biolink:part_of`, and `has_part` $\rightarrow$ `biolink:has_part`.
2. For any other non-IRI predicate, KGX defaults to `fixed_edge["predicate"] = f"biolink:{edge['pred']}"`.
3. Consequently, KGX produced pseudo-Biolink CURIEs: `biolink:inverseOf` and `biolink:subPropertyOf`, which are not valid Biolink slots.

### B. Normalization to W3C Semantic Standards
Rather than dropping these relationship axioms during merge, `ngest` normalizes them to their canonical W3C standards:
* **`owl:inverseOf`** (`http://www.w3.org/2002/07/owl#inverseOf`): Web Ontology Language relation between inverse properties.
* **`rdfs:subPropertyOf`** (`http://www.w3.org/2000/01/rdf-schema#subPropertyOf`): RDF Schema relation defining property subsumption.

Both prefixes (`owl:` and `rdfs:`) are natively supported by the KGX `PrefixManager`.

### C. Implementation
Normalization is executed in each ontology post-processing script:
* `workflow/scripts/cl_kgx_process.py`
* `workflow/scripts/go_kgx_process.py`
* `workflow/scripts/mondo_kgx_process.py`
* `workflow/scripts/uberon_kgx_process.py`

```python
edges["predicate"] = edges["predicate"].replace({
    "biolink:inverseOf": "owl:inverseOf",
    "biolink:subPropertyOf": "rdfs:subPropertyOf",
})
edges["relation"] = edges["relation"].replace({
    "inverseOf": "owl:inverseOf",
    "subPropertyOf": "rdfs:subPropertyOf",
})
```

And both predicates are retained in `config/databases_config.yaml` and `config/merge_config.yaml` under each ontology's `edge_filters.predicate`.

---

## 3. Interaction & Association Predicates (Avoiding Physical Over-Assertion)

A critical distinction in biomedical knowledge graphs is between **direct physical binding** and **functional association / statistical correlation**:

### A. STRING DB (`9606.protein.links.v12.5.txt.gz`)
* **Data Nature**: STRING's primary `protein.links` dataset combines physical interactions with indirect functional associations derived from 7 distinct evidence channels (neighborhood, gene fusion, co-occurrence, co-expression, experimental assays, automated text mining, and database pathways).
* **Semantic Predicate**: Using `biolink:physically_interacts_with` would be a false assertion for links derived from text mining or co-expression. We map STRING edges to **`biolink:interacts_with`** with relation **`RO:0002434`** (*interacts with*), matching Biolink's formal definition:
  > *"Holds between two entities that participate in a physical or functional relationship."*

### B. NPInter
NPInter records functional interactions of non-coding RNAs with proteins, RNAs, and genomic DNA. Predicates are mapped according to the underlying experimental class:
* `"binding"` $\rightarrow$ **`biolink:interacts_with`**: Represents validated binding assays (CLIP-seq, RIP-seq, pulldowns) without over-asserting direct binary physical contact in complex ribonucleoprotein assemblies.
* `"regulatory"` and `"binding;regulatory"` $\rightarrow$ **`biolink:regulates`**: Functional regulation of expression or activity.
* `"expression correlation"` $\rightarrow$ **`biolink:correlated_with`**: Statistical correlation between RNA and gene expression levels (replaces the non-existent `biolink:correlates`).
* `"coexpression"` $\rightarrow$ **`biolink:coexpressed_with`**: Statistical co-expression.

### C. DIANA-TarBase v9.0
* **Source**: [DIANA-TarBase v9.0](https://dianalab.e-ce.uth.gr/tarbasev9/)
* **Citation**: Skoufos, G., et al. (2024). *TarBase-v9.0 extends experimentally supported miRNA–gene interactions to cell-types and virally encoded miRNAs.* Nucleic Acids Res, 52(D1), D204–D210. DOI: [10.1093/nar/gkad1071](https://doi.org/10.1093/nar/gkad1071).
* **Semantic Predicate**: miRNA-target interactions are validated by diverse assays ranging from reporter assays (luciferase) and qPCR to crosslinking (HITS-CLIP, PAR-CLIP, CLASH). They are modeled as **`biolink:interacts_with`** / `biolink:regulates`.

### D. Gene Ontology Annotations (GOA)
* **Qualifier Mapping**: The legacy GOA qualifier `involved_in` is mapped to the canonical Biolink slot **`biolink:actively_involved_in`** (`RO:0002331`).
* **Complexes**: Node category for protein complexes is updated to **`biolink:MacromolecularComplex`** (replacing the deprecated `MacromolecularComplexMixin`).
