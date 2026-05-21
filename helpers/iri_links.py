"""Build canonical Linked Data IRIs for I14Y resources."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

I14Y_REGISTER_BASE_URL = os.getenv(
    "I14Y_REGISTER_BASE_URL",
    "https://register.ld.admin.ch/i14y",
)


def _quote(value: str) -> str:
    return quote(value.strip(), safe="")


def _primary_identifier(item: dict[str, Any]) -> str | None:
    """Return the canonical identifier from I14Y API models.

    According to the API models, resources expose:
    - identifiers: list[str]
    - identifier: str, sometimes deprecated but still present in some responses/search models

    Prefer identifiers[0] when available.
    """
    identifiers = item.get("identifiers")

    if isinstance(identifiers, list):
        for identifier in identifiers:
            if isinstance(identifier, str) and identifier.strip():
                return identifier.strip()

    identifier = item.get("identifier")
    if isinstance(identifier, str) and identifier.strip():
        return identifier.strip()

    return None


def _version(item: dict[str, Any]) -> str | None:
    version = item.get("version")
    if isinstance(version, str) and version.strip():
        return version.strip()
    return None


def build_iri(resource_type: str, item: dict[str, Any]) -> str | None:
    """Build the canonical I14Y Linked Data IRI for a typed API item.

    resource_type must be one of:
    - concept
    - dataset
    - dataservice
    - publicservice
    - mappingtable
    """
    identifier = _primary_identifier(item)
    version = _version(item)

    if not identifier:
        return None

    normalized_type = resource_type.lower().replace("_", "").replace("-", "")

    if normalized_type == "concept":
        if not version:
            return None
        return (
            f"{I14Y_REGISTER_BASE_URL}/concept/"
            f"{_quote(identifier)}/version/{_quote(version)}"
        )

    if normalized_type == "dataset":
        return f"{I14Y_REGISTER_BASE_URL}/dataset/{_quote(identifier)}"

    if normalized_type == "dataservice":
        return f"{I14Y_REGISTER_BASE_URL}/dataservice/{_quote(identifier)}"

    if normalized_type == "publicservice":
        return f"{I14Y_REGISTER_BASE_URL}/publicservice/{_quote(identifier)}"

    if normalized_type == "mappingtable":
        if not version:
            return None
        return (
            f"{I14Y_REGISTER_BASE_URL}/mappingtable/"
            f"{_quote(identifier)}/version/{_quote(version)}"
        )

    return None


def enrich_item_with_iri(item: dict[str, Any], resource_type: str) -> dict[str, Any]:
    enriched = dict(item)
    iri = build_iri(resource_type, item)

    if iri:
        enriched["iri"] = iri

    return enriched


def enrich_response_with_iris(data: Any, resource_type: str) -> Any:
    """Add iri to common response shapes for a known resource type."""
    if isinstance(data, list):
        return [
            enrich_item_with_iri(item, resource_type)
            if isinstance(item, dict)
            else item
            for item in data
        ]

    if isinstance(data, dict):
        enriched = dict(data)

        for key in ("data", "items", "results"):
            value = enriched.get(key)
            if isinstance(value, list):
                enriched[key] = [
                    enrich_item_with_iri(item, resource_type)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
                return enriched

        return enrich_item_with_iri(enriched, resource_type)

    return data


def enrich_catalog_search_result_with_iris(data: Any) -> Any:
    """Add iri to CatalogSearchResult items using their type field.

    CatalogSearchResult exposes type, identifier, and sometimes version.
    """
    def enrich(item: dict[str, Any]) -> dict[str, Any]:
        resource_type = item.get("type")
        if not isinstance(resource_type, str) or not resource_type.strip():
            return item
        return enrich_item_with_iri(item, resource_type)

    if isinstance(data, list):
        return [enrich(item) if isinstance(item, dict) else item for item in data]

    if isinstance(data, dict):
        enriched = dict(data)

        for key in ("data", "items", "results"):
            value = enriched.get(key)
            if isinstance(value, list):
                enriched[key] = [
                    enrich(item) if isinstance(item, dict) else item
                    for item in value
                ]
                return enriched

        return enrich(enriched)

    return data