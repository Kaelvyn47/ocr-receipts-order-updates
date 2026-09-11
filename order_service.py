from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class OrderDocument:
    order_id: str
    pdf: str
    customer_email: str


@dataclass(frozen=True)
class OrderUpdate:
    order_id: str
    searchable_text: str
    customer_email: str
    status: str


def process_receipt(document: OrderDocument, ocr: Callable[..., dict[str, Any]]) -> OrderUpdate:
    result = ocr(document.pdf)
    text = str(result.get("text", "")).strip()
    status = "ready_for_fulfillment" if len(text) >= 20 else "needs_review"
    return OrderUpdate(document.order_id, text, document.customer_email, status)
