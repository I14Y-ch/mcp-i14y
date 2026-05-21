"""MCP tools for full-text search across I14Y resources (via CORE API)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient

__all__ = ["register"]

_VALID_TYPES = {"Dataset", "DataService", "PublicService", "Concept", "MappingTable"}


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="full_text_search_resources")
    async def full_text_search_resources(
        query: str,
        types: list[str] | None = None,
        publishers: list[str] | None = None,
        statuses: list[str] | None = None,
        page: int = 1,
        page_size: int = 25,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """Full-text search I14Y resources by an explicit user-provided query.

        Use this tool only when the user explicitly asks to search or provides a concrete
        search term, title, identifier, acronym, or domain-specific keyword.

        Do not use this tool as a default discovery, browsing, listing, inventory, mapping,
        classification, or schema-matching tool.

        Do not derive search queries automatically from:
        - schema property names
        - TTL/RDF/SHACL property identifiers
        - CSV column names
        - JSON keys
        - database column names
        - local dataset attribute codes
        - arbitrary field labels extracted from user-provided files

        For schema or data-structure mapping tasks, use list_* tools to retrieve a candidate
        set, then compare candidates semantically using labels, descriptions, identifiers,
        publisher, type, datatype, and metadata.

        For concept/codelist mapping, prefer list_concepts(fetch_all=True) or
        list_concept_candidates_for_mapping() over this full-text search tool.

        If the user did not provide a concrete search query, call the relevant list_* tool
        instead.

        Pagination:
            By default this returns one page and includes pagination metadata.
            If fetch_all=True, all available pages are fetched unless max_pages is set.

        Args:
            query: Concrete user-provided search query. Must not be invented or derived from
                local schema/field names.
            types: Optional resource type filter. Valid values: "Dataset", "DataService",
                "PublicService", "Concept", "MappingTable".
            publishers: Optional publisher identifier filter, e.g. ["CH1"].
            statuses: Optional registration status filter.
            page: Page number, starting at 1.
            page_size: Results per page.
            fetch_all: Fetch all pages instead of one page.
            max_pages: Optional maximum pages when fetch_all=True.

        Returns:
            Structured search results with pagination metadata.
        """
        if types:
            invalid = [t for t in types if t not in _VALID_TYPES]
            if invalid:
                return {
                    "error": "Invalid type(s)",
                    "invalid_types": invalid,
                    "valid_values": sorted(_VALID_TYPES),
                }

        common_params = dict(
            query=query,
            types=types,
            publishers=publishers,
            statuses=statuses,
        )

        async with CoreApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    "/Catalog/search",
                    page_size=page_size,
                    max_pages=max_pages,
                    catalog_search=True,
                    **common_params,
                )

            return await client.get(
                "/Catalog/search",
                catalog_search=True,
                page=page,
                pageSize=page_size,
                **common_params,
            )
