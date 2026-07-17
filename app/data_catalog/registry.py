"""Data Source Card validation gate used before publishing serving artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.v2.data_source_card import DataSourceCard


class SourceNotApprovedError(ValueError):
    pass


def load_source_card(path: str | Path) -> DataSourceCard:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return DataSourceCard.model_validate(payload)


def require_serving_approval(path: str | Path) -> DataSourceCard:
    card = load_source_card(path)
    if not card.is_usable_for_serving():
        raise SourceNotApprovedError(f"source {card.source_id} is not approved for serving")
    return card
