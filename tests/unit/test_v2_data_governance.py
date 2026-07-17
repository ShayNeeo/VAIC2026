"""All serving source cards must pass the same governance contract.

data/catalog/source_cards/ is shared with services/rag_mcp/, which registers
its own *_reference_pack.json cards validated by its own, deliberately
simpler services.rag_mcp.ingestion._validate_card (see docs/RAG_MCP_SERVER.md).
Those cards are not compatible with the stricter app.schemas.v2.DataSourceCard
contract (extra="forbid" vs. rag_mcp's flat dataset_version/effective_from
fields) and were never meant to be: this test only covers the cards actually
consumed by the app/ in-process governed catalog (app.knowledge, app.operations,
app.eligibility), enumerated explicitly so a glob over the shared directory
cannot silently pull in an unrelated subsystem's cards again.
"""

from __future__ import annotations

from app.data_catalog.registry import load_source_card
from app.eligibility.registry import DEFAULT_RULES_SOURCE_CARD
from app.knowledge.legal_service import DEFAULT_SOURCE_CARD as LEGAL_KNOWLEDGE_SOURCE_CARD
from app.knowledge.service import DEFAULT_SOURCE_CARD as PRODUCT_CATALOG_SOURCE_CARD
from app.operations.service import DEFAULT_SOP_SOURCE_CARD


def test_every_registered_source_card_is_contract_valid_and_serving_approved():
    paths = sorted(
        {
            PRODUCT_CATALOG_SOURCE_CARD,
            LEGAL_KNOWLEDGE_SOURCE_CARD,
            DEFAULT_SOP_SOURCE_CARD,
            DEFAULT_RULES_SOURCE_CARD,
        }
    )
    assert len(paths) >= 4
    cards = [load_source_card(path) for path in paths]
    assert len({card.source_id for card in cards}) == len(cards)
    assert all(card.is_usable_for_serving() for card in cards)
    assert all(card.owner.business_owner and card.owner.data_steward for card in cards)
    assert all(card.lineage.raw_location and card.quality.required_checks for card in cards)
