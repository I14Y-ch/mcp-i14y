"""MCP tool for reading the content of a DCAT distribution."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from mcp.server.fastmcp import FastMCP

__all__ = ["register"]

logger = logging.getLogger(__name__)

VERSION = "0.1.0"
USER_AGENT = f"mcp-i14y/{VERSION} (https://github.com/I14Y-ch/mcp-i14y)"

# Content types that are safe to read as text
_TEXT_TYPES = {
    "application/json",
    "application/ld+json",
    "application/geo+json",
    "text/csv",
    "text/plain",
    "text/xml",
    "application/xml",
    "application/rdf+xml",
    "text/turtle",
    "application/sparql-results+json",
    "application/sparql-results+xml",
}

# Content types that are binary and cannot be meaningfully returned to an LLM
_BINARY_TYPES = {
    "application/pdf",
    "application/zip",
    "application/gzip",
    "application/x-tar",
    "application/octet-stream",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument",
    "image/",
    "audio/",
    "video/",
}


def _is_binary(content_type: str) -> bool:
    ct = content_type.split(";")[0].strip().lower()
    return any(ct.startswith(bt) for bt in _BINARY_TYPES)


def _is_text(content_type: str) -> bool:
    ct = content_type.split(";")[0].strip().lower()
    return ct.startswith("text/") or any(ct == t for t in _TEXT_TYPES)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_distribution_content(
        download_url: str,
        max_kb: int = 200,
    ) -> dict[str, Any]:
        """Fetch and return the content of a DCAT distribution file.

        Use this after get_dataset() to read the actual data behind a distribution.
        The distribution's downloadUrl.uri (from the get_dataset response) should
        be passed directly as download_url.

        Supports text-based formats: JSON, CSV, XML, RDF/Turtle, GeoJSON, etc.
        Binary formats (PDF, ZIP, Excel, images) are rejected with an error message.
        Content is truncated to max_kb kilobytes if the file is larger.

        Typical workflow:
            1. dataset = get_dataset(dataset_id)
            2. url = dataset["data"]["distributions"][0]["downloadUrl"]["uri"]
            3. content = get_distribution_content(url)

        Args:
            download_url: The direct download URL of the distribution
                (value of downloadUrl.uri from a distribution object).
            max_kb: Maximum content size to return in kilobytes (default 200 KB).
                Larger files are truncated with a warning.

        Returns:
            Structured object containing content metadata and either parsed JSON
            or text content.
        """
        max_bytes = max_kb * 1024

        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()

                    content_type = response.headers.get("content-type", "")
                    ct_base = content_type.split(";")[0].strip().lower()

                    if _is_binary(content_type):
                        return {
                            "error": (
                                f"Binary content type '{ct_base}' cannot be returned as text."
                            ),
                            "url": download_url,
                            "content_type": content_type,
                        }

                    if not _is_text(content_type):
                        return {
                            "error": (
                                f"Unsupported content type '{ct_base}'. "
                                "Only text-like distributions can be returned."
                            ),
                            "url": download_url,
                            "content_type": content_type,
                        }

                    chunks: list[bytes] = []
                    total = 0
                    truncated = False

                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        if total + len(chunk) > max_bytes:
                            remaining = max_bytes - total
                            chunks.append(chunk[:remaining])
                            truncated = True
                            break
                        chunks.append(chunk)
                        total += len(chunk)

                    text = b"".join(chunks).decode("utf-8", errors="replace")

                    result: dict[str, Any] = {
                        "url": download_url,
                        "content_type": content_type,
                        "truncated": truncated,
                        "max_kb": max_kb,
                    }

                    if "json" in ct_base:
                        try:
                            result["data"] = json.loads(text)
                        except Exception:
                            result["text"] = text
                    else:
                        result["text"] = text

                    if truncated:
                        result["warning"] = (
                            f"Content exceeds {max_kb} KB. Only the first {max_kb} KB "
                            "are shown."
                        )

                    return result

        except httpx.HTTPStatusError as exc:
            return {
                "error": f"HTTP {exc.response.status_code} fetching distribution",
                "url": download_url,
            }
        except httpx.RequestError as exc:
            return {
                "error": f"Network error fetching distribution: {exc}",
                "url": download_url,
            }
