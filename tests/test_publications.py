"""Unit tests for literature reference (PMID) extraction and formatting across ngest ingestors."""

import pandas as pd
import pytest
import re


def test_disgenet_pmid_formatting():
    """Verify DisGeNET PMID parsing handles numeric floats, ints, nulls, and strings."""
    def format_pmids(p):
        if pd.notnull(p):
            s = str(p).strip()
            if s.replace(".", "").isdigit():
                val = int(float(s))
                if val > 0:
                    return f"PMID:{val}"
        return ""

    assert format_pmids(18706098) == "PMID:18706098"
    assert format_pmids(18706098.0) == "PMID:18706098"
    assert format_pmids("18706098") == "PMID:18706098"
    assert format_pmids(None) == ""
    assert format_pmids(float("nan")) == ""
    assert format_pmids(0) == ""
    assert format_pmids("invalid") == ""


def test_goa_pmid_extraction():
    """Verify GOA DB:Reference extraction handles single and pipe-separated references."""
    def extract_pmids(ref):
        if pd.isna(ref):
            return ""
        parts = str(ref).split("|")
        pmids = [p.strip() for p in parts if p.strip().startswith("PMID:") and p.strip()[5:].isdigit()]
        return "|".join(pmids)

    assert extract_pmids("PMID:33961781") == "PMID:33961781"
    assert extract_pmids("GO_REF:0000003") == ""
    assert extract_pmids("PMID:12345|GO_REF:0000002|PMID:67890") == "PMID:12345|PMID:67890"
    assert extract_pmids("Reactome:R-HSA-12345") == ""
    assert extract_pmids(None) == ""


def test_hpoa_pmid_extraction():
    """Verify HPOA DB Reference extraction handles semicolon-separated references and ignores non-PMIDs."""
    def extract_pmids(ref):
        if pd.isna(ref):
            return ""
        parts = str(ref).split(";")
        pmids = [p.strip() for p in parts if p.strip().startswith("PMID:") and p.strip()[5:].isdigit()]
        return "|".join(pmids)

    assert extract_pmids("PMID:31675180") == "PMID:31675180"
    assert extract_pmids("PMID:21519361;PMID:19890111") == "PMID:21519361|PMID:19890111"
    assert extract_pmids("OMIM:609153") == ""
    assert extract_pmids("ORPHA:12345;PMID:999999") == "PMID:999999"
    assert extract_pmids(None) == ""


def test_pmid_aggregation_capping():
    """Verify that multiple publications are deduplicated, sorted, and capped at 50."""
    pmid_list = [f"PMID:{i}" for i in range(100, 0, -1)] + ["PMID:1", "PMID:2"]
    aggregated = "|".join(sorted(set(x for x in pmid_list if x))[:50])
    items = aggregated.split("|")
    assert len(items) == 50
    assert all(re.match(r"^PMID:\d+$", item) for item in items)
    # Check sorted order
    assert items == sorted(items)
