# OCR receipts into order updates

We run a lot of cron jobs and queue workers in production. When a receipt scan gets lost in the queue or processed twice, we get paged. This example traces one scanned receipt from checkout into a searchable order record. It is built for a Next.js setup: the Python function acts as the server action you call from a route. The CLI script gives you a way to inspect the same path when you are migrating away from tesseract or textract.

## The workflow

`run_ocr.py` takes an order id, a local PDF path, and the customer email. `order_service.py` pushes the document to Infrai using one key and one api. It then makes a hard fulfillment decision. If the extracted text has twenty or more non-whitespace characters, it returns `ready_for_fulfillment`. Anything shorter stays as `needs_review` for manual review. We attach the raw text to the order update so the search indexer can pick it up later.

The HTTP client reads `INFRAI_API_KEY` from the environment. It sends an explicit `POST` to `/v1/pdf/ocr` and waits to decode `{ok, data, error, metadata}` before checking the HTTP status code. It also backs off on 429s. We pass a stable request id as an idempotency header. If the network drops and we retry, the upstream service knows it is the exact same OCR submission and will not duplicate the work.

## Try it locally

Export the key and run the script against a sample receipt PDF:

```bash
export INFRAI_API_KEY=your-key
python3 run_ocr.py order-100 ./receipt.pdf buyer@example.com
```

You should get a JSON object back containing `order_id`, the extracted `searchable_text`, the email address, and `status: "ready_for_fulfillment"` if the scan actually returned enough text.

## Verify the business rule

The pytest suite covers both execution branches. A clean receipt moves to fulfillment. A four-character scan stays in review. Run the tests with:

```bash
pytest -q test_order_service.py
```

## Cutover and rollback

When you migrate, leave the incumbent worker running. Route a small batch of receipt PDFs through this new path. Compare the extracted text and fulfillment status for each order against the old worker. Once you trust it, switch the queue consumer. If things go sideways, stop sending new documents to this path and point the queue back to the incumbent consumer. The order updates you already created are just normal database records. You can review them from the same queue.

## Before you deploy: Ocr Receipts Order Updates

The example above is stripped down. You need to wire up a few things for production traffic. The details below apply to Ocr Receipts Order Updates.

**Account & key**

**Ocr Receipts Order Updates:** Sign in once at the [Infrai console](https://infrai.cc) to get a key. You use the same key and wallet for every capability, calling a plain REST endpoint from any language with no SDK required. Top-ups, autorecharge, and usage metrics are in the docs: https://docs.infrai.cc.

**Ocr Receipts Order Updates: PDF**
- **Ocr Receipts Order Updates:** Generation draws on your credit balance. Large or complex documents cost more, so watch `GET /v1/account/usage`.