"""MCP tools for I14Y Concepts (codelists, data dictionaries)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient
from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_concepts(
        publisher_identifier: str | None = None,
        concept_identifier: str | None = None,
        version: str | None = None,
        registration_status: str | None = None,
        publication_level: str | None = None,
        page: int = 1,
        page_size: int = 25,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """List data concepts (codelists, data dictionaries) on the Swiss I14Y platform.

        Concepts are reusable data definitions that ensure semantic interoperability
        across Swiss government systems. They include codelists (e.g. country codes,
        canton codes), date formats, numeric ranges, and string patterns.

        Pagination:
            By default this returns one page and includes pagination metadata from
            the API response headers. If fetch_all=True, all available pages are
            fetched unless max_pages is set. Use fetch_all=True only when the user
            explicitly asks for all matching concepts or a complete scan.

        Args:
            publisher_identifier: Filter by the publishing organisation's identifier.
            concept_identifier: Filter by the concept's own identifier.
            version: Filter by concept version string.
            registration_status: One of Initial, Candidate, Recorded, Qualified,
                Standard, PreferredStandard, Superseded, Retired.
            publication_level: "Internal" or "Public".
            page: Page number (starts at 1).
            page_size: Number of results per page (default 25).
            fetch_all: Fetch all pages instead of only one page.
            max_pages: Optional maximum number of pages to fetch when fetch_all=True.

        Returns:
            JSON string with concept results and pagination metadata.
        """
        common_params = dict(
            publisherIdentifier=publisher_identifier,
            conceptIdentifier=concept_identifier,
            version=version,
            registrationStatus=registration_status,
            publicationLevel=publication_level,
        )

        async with I14YApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    "/concepts",
                    page_size=page_size,
                    max_pages=max_pages,
                    resource_type="concept",
                    **common_params,
                )

            return await client.get(
                "/concepts",
                resource_type="concept",
                page=page,
                pageSize=page_size,
                **common_params,
            )
        
    @mcp.tool()
    async def list_concept_candidates_for_mapping(
        publisher_identifier: str | None = None,
        publication_level: str | None = "Public",
        page_size: int = 100,
    ) -> dict:
        """List concept candidates for schema, field, attribute, or codelist mapping.

        Use this tool when the user provides a data structure, schema, TTL/RDF/SHACL,
        CSV headers, JSON schema, database schema, or a list of attributes and asks to
        map fields to I14Y concepts, codelists, identifiers, or conformsTo references.

        This tool retrieves the candidate concept set. The model should then compare
        the user's fields against the returned concepts by semantic meaning using labels,
        descriptions, identifiers, publisher, concept type, datatype, and metadata.

        Prefer this tool over full_text_search_resources for mapping tasks, because
        field names and local attribute codes are often not reliable search queries.

        Args:
            publisher_identifier: Optional publisher filter.
            publication_level: Optional publication level filter. Defaults to "Public".
            page_size: Number of results per page while fetching all pages.

        Returns:
            All matching concept candidates with pagination metadata.
        """
        async with I14YApiClient() as client:
            return await client.get_all_pages(
                "/concepts",
                page_size=page_size,
                max_pages=None,
                resource_type="concept",
                publisherIdentifier=publisher_identifier,
                publicationLevel=publication_level,
            )

    @mcp.tool()
    async def get_concept(
        concept_id: str,
        include_codelist_entries: bool = False,
    ) -> dict:
        """Get detailed metadata for a specific data concept.

        Args:
            concept_id: The unique identifier of the concept.
            include_codelist_entries: If True, embed all codelist entries in the response.
                Use get_concept_codelist for large codelists to avoid oversized responses.

        Returns:
            JSON string with concept metadata and optionally its codelist entries.
        """
        async with I14YApiClient() as client:
            return await client.get(
                f"/concepts/{concept_id}",
                resource_type="concept",
                includeCodeListEntries=str(include_codelist_entries).lower(),
            )

    @mcp.tool()
    async def get_concept_codelist(
        concept_id: str,
        format: str = "json",
    ) -> dict:
        """Export all codelist entries for a concept.

        Use this tool to retrieve the full set of valid values defined by a codelist concept
        (e.g. all canton codes, all country codes).

        Args:
            concept_id: The unique identifier of the concept.
            format: Export format — "json" (default) or "csv".

        Returns:
            Codelist entries as a JSON array or CSV text.
        """
        valid = {"json", "csv"}
        if format not in valid:
            return {"error": f"Invalid format '{format}'", "valid_values": sorted(valid)}

        async with I14YApiClient() as client:
            return await client.get(f"/concepts/{concept_id}/codelist-entries/exports/{format}")

    @mcp.tool()
    async def get_concept_by_identifier(identifier: str) -> dict:
        """Get concept(s) by their human-readable identifier (e.g. "HGDE_KT").

        Unlike get_concept() which requires a UUID, this tool accepts the short identifier
        string visible in the I14Y platform and URLs. Returns all versions of the concept
        with that identifier.

        Args:
            identifier: The concept identifier string (e.g. "HGDE_KT", "CL_NOGA").

        Returns:
            JSON array of concepts matching the identifier, with full metadata.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/Concepts/identifier/{identifier}")

    @mcp.tool()
    async def get_codelist_entries(
        concept_id: str,
        page: int = 1,
        page_size: int = 100,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """Get codelist entries with full annotations for a concept.

        Returns richer data than get_concept_codelist() — includes annotations,
        descriptions, and hierarchical metadata for each entry.

        Pagination:
            By default this returns one page and includes pagination metadata from
            the API response headers. If fetch_all=True, all available pages are
            fetched unless max_pages is set.

        Args:
            concept_id: The unique identifier (UUID) of the concept.
            page: Page number (starts at 1).
            page_size: Results per page (default 100).
            fetch_all: Fetch all pages instead of only one page.
            max_pages: Optional maximum number of pages to fetch when fetch_all=True.

        Returns:
            JSON object with codelist entries and pagination metadata.
        """
        async with CoreApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    f"/Concepts/{concept_id}/codelist-entries",
                    page_size=page_size,
                    max_pages=max_pages,
                )

            return await client.get(
                f"/Concepts/{concept_id}/codelist-entries",
                page=page,
                pageSize=page_size,
            )

    @mcp.tool()
    async def get_codelist_entry_by_code(concept_id: str, code: str) -> dict:
        """Get a single codelist entry by its code value.

        Use this to look up the label and metadata for a specific code, e.g. find what
        canton code "1" means in HGDE_KT.

        Args:
            concept_id: The unique identifier (UUID) of the concept.
            code: The code value to look up (e.g. "1", "CH", "A").

        Returns:
            JSON object with the matching codelist entry (code, label, description).
        """
        async with CoreApiClient() as client:
            return await client.get(
                f"/Concepts/{concept_id}/codelist-entries/by-code",
                code=code,
            )

    @mcp.tool()
    async def get_codelist_entries_children(
        concept_id: str,
        parent_code: str,
        page: int = 1,
        page_size: int = 100,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """Get all child entries of a parent code in a hierarchical codelist.

        For codelists with a parent-child hierarchy (e.g. NUTS regions, Swiss
        commune/district/canton hierarchy), this returns all direct children of a
        given parent code.

        Pagination:
            By default this returns one page and includes pagination metadata from
            the API response headers. If fetch_all=True, all available pages are
            fetched unless max_pages is set.

        Args:
            concept_id: The unique identifier (UUID) of the concept.
            parent_code: The parent code whose children to retrieve.
            page: Page number (starts at 1).
            page_size: Results per page (default 100).
            fetch_all: Fetch all pages instead of only one page.
            max_pages: Optional maximum number of pages to fetch when fetch_all=True.

        Returns:
            JSON object with child codelist entries and pagination metadata.
        """
        async with CoreApiClient() as client:
            common_params = dict(parentCode=parent_code)

            if fetch_all:
                return await client.get_all_pages(
                    f"/Concepts/{concept_id}/codelist-entries/children-of",
                    page_size=page_size,
                    max_pages=max_pages,
                    **common_params,
                )

            return await client.get(
                f"/Concepts/{concept_id}/codelist-entries/children-of",
                page=page,
                pageSize=page_size,
                **common_params,
            )

    @mcp.tool()
    async def search_codelist_entries(
        concept_id: str,
        query: str,
        language: str = "fr",
        page: int = 1,
        page_size: int = 25,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """Search for entries within a specific codelist by label or code.

        Use this to find specific codes within a large codelist without fetching all
        entries. For example, find the code for "Zurich" in the canton codelist, or
        search for a specific NOGA sector.

        Pagination:
            By default this returns one page and includes pagination metadata from
            the API response headers. If fetch_all=True, all available pages are
            fetched unless max_pages is set.

        Args:
            concept_id: The unique identifier (UUID) of the concept.
            query: Search term to match against entry labels or codes.
            language: Language for label matching — "fr", "de", "it", or "en" (default "fr").
            page: Page number (starts at 1).
            page_size: Results per page (default 25).
            fetch_all: Fetch all pages instead of only one page.
            max_pages: Optional maximum number of pages to fetch when fetch_all=True.

        Returns:
            JSON object with matching codelist entries and pagination metadata.
        """
        common_params = dict(language=language, query=query)

        async with CoreApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    f"/Concepts/{concept_id}/codelist-entries/search",
                    page_size=page_size,
                    max_pages=max_pages,
                    **common_params,
                )

            return await client.get(
                f"/Concepts/{concept_id}/codelist-entries/search",
                page=page,
                pageSize=page_size,
                **common_params,
            )
