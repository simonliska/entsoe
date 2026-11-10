"""Minimal HTTP client for the ENTSO-E Transparency Platform REST API."""

import io
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

API_URL = "https://web-api.tp.entsoe.eu/api"
RETRY_STATUS = {429, 500, 502, 503, 504}

logger = logging.getLogger(__name__)


def fetch(params: dict[str, str], token: str, *, retries: int = 3, timeout: int = 30) -> bytes:
    """GET the API with ``params``. The token goes in a header, so it never appears in URLs/logs."""
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"SECURITY_TOKEN": token})

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRY_STATUS or attempt == retries:
                body = exc.read()
                if body.lstrip().startswith(b"<"):
                    return body
                raise
        except urllib.error.URLError:
            if attempt == retries:
                raise
        logger.warning("Request failed, retrying", extra={"attempt": attempt, "url": url})
        time.sleep(2**attempt)
    raise RuntimeError("unreachable")


def documents(body: bytes) -> list[bytes]:
    """Some endpoints return a ZIP of XML documents; normalise to a list of XML documents."""
    if not body.startswith(b"PK"):
        return [body]
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        return [archive.read(name) for name in archive.namelist() if name.endswith(".xml")]
