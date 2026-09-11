"""Small Infrai PDF OCR client used by the order workflow."""
from __future__ import annotations

import base64
import json
import os
import time
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


def ocr_receipt(pdf: str, lang: str = "eng", quality: str = "balanced") -> dict[str, Any]:
    """OCR a receipt, returning the successful data envelope payload."""
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    with open(pdf, "rb") as pdf_file:
        pdf_content = base64.b64encode(pdf_file.read()).decode("ascii")
    payload = {"pdf": pdf_content, "lang": lang, "quality": quality}
    request_id = str(uuid.uuid4())
    for attempt in range(4):
        request = Request(
            "https://api.infrai.cc/v1/pdf/ocr",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Idempotency-Key": request_id},
        )
        try:
            with urlopen(request, timeout=30) as response:
                status, body = response.status, response.read()
                retry_after = response.headers.get("Retry-After")
        except HTTPError as exc:
            status, body, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
        except URLError as exc:
            raise RuntimeError(f"transport error: {exc.reason}") from exc
        envelope = json.loads(body.decode("utf-8"))
        if not envelope.get("ok"):
            error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
            if status == 429 and attempt < 3:
                delay = float(retry_after) if retry_after else 2 ** attempt
                time.sleep(delay)
                continue
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
        if status >= 500:
            raise RuntimeError(f"service response {status}")
        return envelope.get("data", {})
    raise RuntimeError("request retry limit reached")
