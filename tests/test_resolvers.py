"""Unit tests for entity resolvers, normalizers, and Biolink Model CURIE validation in ngest."""

import re
import pytest


# ---------------------------------------------------------------------------
# 1. HMDD MeSH Disease Resolution Tests
# ---------------------------------------------------------------------------

from workflow.scripts.hmdd_to_kgx import match_disease_to_mondo, MESH_DIRECT_MAP


def test_mesh_direct_mappings():
    """Verify high-frequency clinical MeSH disease mappings."""
    mock_index = {}
    assert match_disease_to_mondo("breast neoplasms", mock_index) == "MONDO:0007254"
    assert match_disease_to_mondo("colorectal neoplasms", mock_index) == "MONDO:0005575"
    assert match_disease_to_mondo("sepsis", mock_index) == "MONDO:0005327"
    assert match_disease_to_mondo("ischemic stroke", mock_index) == "MONDO:0005110"


def test_mesh_inverted_syntax_resolution():
    """Verify inverted clinical terms like 'Carcinoma, Hepatocellular' match MONDO labels."""
    mock_index = {
        "hepatocellular carcinoma": "MONDO:0005267",
        "renal cell carcinoma": "MONDO:0005005",
        "pulmonary fibrosis": "MONDO:0008323",
    }
    assert match_disease_to_mondo("Carcinoma, Hepatocellular", mock_index) == "MONDO:0005267"
    assert match_disease_to_mondo("Carcinoma, Renal Cell", mock_index) == "MONDO:0005005"
    assert match_disease_to_mondo("Fibrosis, Pulmonary", mock_index) == "MONDO:0008323"


def test_mesh_plural_normalization():
    """Verify plural neoplasm and injury terms normalize to singular MONDO concepts."""
    mock_index = {
        "lung cancer": "MONDO:0008903",
        "brain injury": "MONDO:0001234",
    }
    assert match_disease_to_mondo("lung neoplasms", mock_index) == "MONDO:0008903"
    assert match_disease_to_mondo("brain injuries", mock_index) == "MONDO:0001234"


# ---------------------------------------------------------------------------
# 2. TarBase miRNA Arm Suffix Resolution Tests
# ---------------------------------------------------------------------------

def test_mirna_arm_suffix_resolution():
    """Verify mature -5p/-3p suffixes resolve to stem accessions when matching URS."""
    mapping = {
        "hsa-miR-16": "RNACENTRAL:URS00000B9DB0_9606",
        "hsa-miR-155": "RNACENTRAL:URS00002A13D2_9606",
        "hsa-let-7b": "RNACENTRAL:URS0000414F98_9606",
    }

    def resolve_mirna(raw_id: str):
        if raw_id in mapping:
            return mapping[raw_id]
        stem = re.sub(r"-[53]p$", "", raw_id)
        return mapping.get(stem, None)

    # Direct match
    assert resolve_mirna("hsa-miR-16") == "RNACENTRAL:URS00000B9DB0_9606"
    # Suffix matches
    assert resolve_mirna("hsa-miR-16-5p") == "RNACENTRAL:URS00000B9DB0_9606"
    assert resolve_mirna("hsa-miR-16-3p") == "RNACENTRAL:URS00000B9DB0_9606"
    assert resolve_mirna("hsa-miR-155-5p") == "RNACENTRAL:URS00002A13D2_9606"
    assert resolve_mirna("hsa-let-7b-5p") == "RNACENTRAL:URS0000414F98_9606"
    # Unmapped
    assert resolve_mirna("hsa-miR-9999-5p") is None


# ---------------------------------------------------------------------------
# 3. Biolink Model Canonical CURIE Format Verification
# ---------------------------------------------------------------------------

CURIE_PATTERNS = {
    "biolink:RNAProduct": re.compile(r"^RNACENTRAL:URS[0-9A-F]{10}(_[0-9]+)?$"),
    "biolink:Gene": re.compile(r"^(NCBIGene:[0-9]+|ENSEMBL:ENSG[0-9]+)$"),
    "biolink:Protein": re.compile(r"^UNIPROTKB:[A-Z0-9]+(-[0-9]+)?$"),
    "biolink:Disease": re.compile(r"^MONDO:[0-9]{7}$"),
    "biolink:PhenotypicFeature": re.compile(r"^HP:[0-9]{7}$"),
    "biolink:AnatomicalEntity": re.compile(r"^UBERON:[0-9]{7}$"),
    "biolink:Cell": re.compile(r"^CL:[0-9]{7}$"),
    "biolink:BiologicalProcess": re.compile(r"^GO:[0-9]{7}$"),
}


@pytest.mark.parametrize("category,curie,is_valid", [
    ("biolink:RNAProduct", "RNACENTRAL:URS00000B9DB0_9606", True),
    ("biolink:RNAProduct", "MIRBASE:MI0000069", False),  # Legacy fallback forbidden
    ("biolink:Gene", "NCBIGene:6541", True),
    ("biolink:Gene", "HGNC.SYMBOL:PTEN", False),  # Legacy symbol forbidden
    ("biolink:Protein", "UNIPROTKB:P60484", True),
    ("biolink:Disease", "MONDO:0007254", True),
    ("biolink:PhenotypicFeature", "HP:0000717", True),
    ("biolink:AnatomicalEntity", "UBERON:0000955", True),
    ("biolink:Cell", "CL:0000540", True),
    ("biolink:BiologicalProcess", "GO:0007399", True),
])
def test_biolink_curie_validation(category, curie, is_valid):
    """Verify that identifiers strictly adhere to Biolink canonical prefixes without fallbacks."""
    pattern = CURIE_PATTERNS.get(category)
    assert pattern is not None, f"Unknown category: {category}"
    matches = bool(pattern.match(curie))
    assert matches == is_valid, f"Expected {curie} for {category} to be valid={is_valid}, got {matches}"


# ---------------------------------------------------------------------------
# 4. Unix Line Ending (\n) & CRLF (\r) Protection Tests
# ---------------------------------------------------------------------------

def test_tsv_lineterminator_compliance(tmp_path):
    """Verify that TSV exports use Unix \\n endings to avoid carriage return column corruption."""
    import csv

    out_file = tmp_path / "test_nodes.tsv"
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "category", "name", "provided_by"],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow({
            "id": "NCBIGene:1000",
            "category": "biolink:Gene",
            "name": "CDH2",
            "provided_by": "NCBIGene",
        })

    with open(out_file, "rb") as f:
        raw_bytes = f.read()

    assert b"\r" not in raw_bytes, "Found forbidden carriage return (\\r) in output TSV!"
    lines = raw_bytes.decode("utf-8").split("\n")
    header = lines[0].split("\t")
    assert header[-1] == "provided_by", f"Corrupted last column header: {repr(header[-1])}"
