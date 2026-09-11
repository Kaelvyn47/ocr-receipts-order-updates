from order_service import OrderDocument, process_receipt


def test_clear_receipt_moves_order_to_fulfillment():
    document = OrderDocument("ord-42", "receipt.pdf", "buyer@example.com")

    def fake_ocr(pdf: str):
        assert pdf == "receipt.pdf"
        return {"text": "Order 42\nPaid\nTotal 39.90 USD"}

    update = process_receipt(document, fake_ocr)
    assert update.status == "ready_for_fulfillment"
    assert update.searchable_text.startswith("Order 42")


def test_short_scan_stays_in_review():
    document = OrderDocument("ord-43", "blurred.pdf", "buyer@example.com")
    update = process_receipt(document, lambda _: {"text": "Paid"})
    assert update.status == "needs_review"
