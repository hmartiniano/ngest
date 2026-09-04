// ==============================================================================
// NGEST: Sample Neo4j Cypher Queries for Biomedical Knowledge Graph Exploration
// ==============================================================================

// ------------------------------------------------------------------------------
// Query 1: Autism Spectrum Disorder (ASD) - ncRNA Regulatory Path Retrieval
// Finds non-coding RNAs that interact with genes associated with ASD (HP:0000717),
// aggregating path counts and listing target genes.
// ------------------------------------------------------------------------------
MATCH (p:NamedThing {id: 'HP:0000717'})<-[:associated_with]-(g:Gene)<-[r:interacts_with]-(rna:RNAProduct)
RETURN rna.name AS ncRNA_Name,
       rna.id AS RNACentral_ID,
       count(DISTINCT g) AS ASD_Target_Genes_Count,
       collect(DISTINCT g.name)[..10] AS Sample_Target_Genes
ORDER BY ASD_Target_Genes_Count DESC
LIMIT 20;


// ------------------------------------------------------------------------------
// Query 2: Directly Validated miRNA-Target Interactions (DIANA-TarBase)
// Filters interactions validated by direct low-throughput assays (e.g. Luciferase,
// qPCR, Western Blot) and retrieves the supporting PubMed citations.
// ------------------------------------------------------------------------------
MATCH (rna:RNAProduct)-[e:interacts_with {knowledge_source: 'DIANA-TarBase'}]->(g:Gene)
WHERE e.validation_type = 'Direct'
RETURN rna.name AS miRNA,
       g.name AS Target_Gene,
       e.assay_type AS Assay_Method,
       e.publications AS PubMed_Citations
LIMIT 25;


// ------------------------------------------------------------------------------
// Query 3: High-Confidence Protein-Protein Interactions (STRING DB)
// Queries physical/functional protein interactions filtered by normalized confidence
// score (>= 0.7, corresponding to combined score >= 700 in STRING DB).
// ------------------------------------------------------------------------------
MATCH (p1:Protein)-[e:interacts_with {knowledge_source: 'STRING'}]-(p2:Protein)
WHERE e.confidence_score >= 0.700
RETURN p1.name AS Protein_A,
       p2.name AS Protein_B,
       e.confidence_score AS Confidence_Score,
       e.has_confidence_level AS STRING_Combined_Score
ORDER BY e.confidence_score DESC
LIMIT 25;


// ------------------------------------------------------------------------------
// Query 4: Brain-Specific Gene Expression with Direct ncRNA Regulation
// Discovers genes expressed in the Brain (UBERON:0000955) with gold-standard call
// quality, regulated by directly validated microRNAs.
// ------------------------------------------------------------------------------
MATCH (brain:AnatomicalEntity {id: 'UBERON:0000955'})<-[exp:expressed_in]-(g:Gene)<-[reg:interacts_with]-(rna:RNAProduct)
WHERE exp.call_quality = 'gold quality'
  AND reg.validation_type = 'Direct'
RETURN brain.name AS Anatomy,
       g.name AS Expressed_Gene,
       exp.expression_score AS Expression_Score,
       rna.name AS Regulating_miRNA,
       reg.assay_type AS Validation_Assay
ORDER BY exp.expression_score DESC
LIMIT 25;


// ------------------------------------------------------------------------------
// Query 5: Full Disease-Gene-Protein-ncRNA Multi-layer Cascade
// Identifies regulatory cascades from a disease (e.g. Autism MONDO:0005260 or
// Schizophrenia MONDO:0005090) through associated genes, interactome proteins,
// and controlling ncRNAs.
// ------------------------------------------------------------------------------
MATCH (d:Disease {id: 'MONDO:0005260'})<-[:associated_with]-(g:Gene)
MATCH (g)-[ppi:interacts_with {knowledge_source: 'STRING'}]-(p:Protein)
WHERE ppi.confidence_score >= 0.8
MATCH (g)<-[ncrna_rel:interacts_with]-(rna:RNAProduct)
RETURN d.name AS Disease,
       g.name AS Core_Gene,
       p.name AS Interacting_Protein,
       rna.name AS Upstream_ncRNA,
       ncrna_rel.knowledge_source AS ncRNA_Source
LIMIT 25;
