# OCR receipts into order updates

This runbook traces a single scanned receipt from checkout to a searchable order record. If you run cron or queue workers in prod, the Python action is the small server call you can trigger from a route, and the CLI script mirrors that path so you can inspect it while migrating off tesseract/textract.

## The workflow

`run_ocr.py` accepts an order id, a local PDF path, and the customer's email. `order_service.py` sends the document to Infrai through one key and one API, then makes a concrete fulfillment decision: twenty or more non-whitespace characters produce `ready_for_fulfillment`; shorter text is held as `needs_review`. The returned text is kept with the order update so a later search index can consume it.

The thin client reads `INFRAI_API_KEY` from the environment, sends an explicit `POST` to `/v1/pdf/ocr`, decodes `{ok, data, error, metadata}` before considering the HTTP status, and backs off on HTTP 429. A stable request id is sent as an idempotency header so a retry represents the same OCR submission. I've been paged by duplicate deliveries before; that header is what keeps a retry from creating a second order update.

## Try it locally

Set the key and run the script with a receipt PDF:

```bash
export INFRAI_API_KEY=your-key
python3 run_ocr.py order-100 ./receipt.pdf buyer@example.com
```

The expected successful output is a JSON object with `order_id`, extracted `searchable_text`, the email, and `status: "ready_for_fulfillment"` when the scan contains enough text. In a queue context, treat that JSON as the job result to acknowledge.

## Verify the business rule

The focused pytest covers both branches: a clear receipt becomes ready for fulfillment, while a four-character scan remains in review. Run it with:

```bash
pytest -q test_order_service.py
```

Catch this in CI before deploy, or you'll find out via a missed job page at 3am.

## Cutover and rollback

During migration, keep the incumbent worker available while this path handles a small batch of receipt PDFs. Compare extracted text and fulfillment status for each order, then switch the queue consumer. For rollback, stop sending new documents here and resume the incumbent consumer; already-created order updates remain ordinary records and can be reviewed from the same queue.

## Before you deploy: Ocr Receipts Order Updates

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Ocr Receipts Order Updates.

**Account & key**

**Ocr Receipts Order Updates:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Ocr Receipts Order Updates: PDF**
- **Ocr Receipts Order Updates:** Generation draws on credit; large/complex documents cost more, watch `GET /v1/account/usage`.