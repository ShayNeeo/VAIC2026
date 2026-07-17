"""Catalog unit tests: enum, need keywords, compatibility graph, lookups."""

from servers.v3_product_agent.product.catalog import (
    V3_PRODUCT_CATALOG,
    ProductNeed,
    NEED_KEYWORDS,
    COMPATIBILITY_GRAPH,
    get_entry,
    fee_value,
    source_ref,
)


def test_catalog_has_four_products():
    assert set(V3_PRODUCT_CATALOG) == {
        "PROD-PAYROLL",
        "PROD-CASH-MGMT",
        "PROD-COLLECTION",
        "PROD-WORKING-CAPITAL",
    }


def test_every_entry_has_source_metadata():
    required = {"document", "section", "version", "owner", "tier"}
    for pid, entry in V3_PRODUCT_CATALOG.items():
        assert required <= set(entry["source_metadata"]), pid


def test_need_keywords_cover_all_needs():
    assert set(NEED_KEYWORDS) == set(ProductNeed)


def test_compat_graph_references_real_products():
    valid = set(V3_PRODUCT_CATALOG)
    for pid, graph in COMPATIBILITY_GRAPH.items():
        assert pid in valid
        assert set(graph["compatible"]) <= valid
        assert set(graph["exclusion"]) <= valid


def test_fee_value_returns_exact_catalog_value():
    val, unit = fee_value("PROD-WORKING-CAPITAL", "interest_rate")
    assert val == 8.5
    assert unit == "%/year"


def test_fee_value_unknown_returns_none():
    assert fee_value("PROD-PAYROLL", "nonexistent_fee") is None


def test_source_ref_citation_anchor():
    ref = source_ref("PROD-PAYROLL")
    assert ref["source_document_id"] == "Product_Catalog_v3.pdf"
    assert ref["source_section"] == "Payroll"
    assert ref["owner"] == "Product Team"


def test_get_entry_fails_loud_on_unknown():
    try:
        get_entry("PROD-NOPE")
        assert False, "expected KeyError"
    except KeyError:
        pass
