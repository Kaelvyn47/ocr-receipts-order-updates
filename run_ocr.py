"""Run one receipt through OCR and print the customer-order update."""
import argparse
import json

from order_service import OrderDocument, process_receipt
from receipt_sender import ocr_receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR a scanned e-commerce receipt")
    parser.add_argument("order_id")
    parser.add_argument("pdf")
    parser.add_argument("customer_email")
    args = parser.parse_args()
    update = process_receipt(OrderDocument(args.order_id, args.pdf, args.customer_email), ocr_receipt)
    print(json.dumps(update.__dict__, indent=2))


if __name__ == "__main__":
    main()
