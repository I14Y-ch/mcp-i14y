"""MCP tools for I14Y MappingTables.

A MappingTable defines a correspondence between two codelists (source → target),
allowing semantic alignment across different classification systems. For example,
mapping old canton codes to new ones, or aligning a Swiss codelist to a European standard.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_mappingtables(
        publisher_identifier: str | None = None,
        mappingtable_identifier: str | None = None,
        version: str | None = None,
        registration_status: str | None = None,
        publication_level: str | None = None,
        page: int = 1,
        page_size: int = 25,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """List mapping tables registered on the Swiss I14Y platform.

        A mapping table defines a correspondence between two codelists (source → target),
        enabling semantic alignment across different classification systems. For example,
        mapping Swiss canton codes to NUTS regional codes, or aligning one version of a
        codelist to another.

        Pagination:
            By default this returns one page and includes pagination metadata from
            the API response headers. If fetch_all=True, all available pages are
            fetched unless max_pages is set. Use fetch_all=True only when the user
            explicitly asks for all matching mapping tables or a complete scan.

        Args:
            publisher_identifier: Filter by the publishing organisation's identifier.
            mappingtable_identifier: Filter by the mapping table's own identifier.
            version: Filter by version string.
            registration_status: One of Initial, Candidate, Recorded, Qualified,
                Standard, PreferredStandard, Superseded, Retired.
            publication_level: "Internal" or "Public".
            page: Page number (starts at 1).
            page_size: Number of results per page (default 25).
            fetch_all: Fetch all pages instead of only one page.
            max_pages: Optional maximum number of pages to fetch when fetch_all=True.

        Returns:
            JSON string with mapping table results and pagination metadata.
        """
        common_params = dict(
            publisherIdentifier=publisher_identifier,
            mappingTableIdentifier=mappingtable_identifier,
            version=version,
            registrationStatus=registration_status,
            publicationLevel=publication_level,
        )

        async with I14YApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    "/mappingtables",
                    page_size=page_size,
                    max_pages=max_pages,
                    resource_type="mappingtable",
                    **common_params,
                )

            return await client.get(
                "/mappingtables",
                page=page,
                pageSize=page_size,
                resource_type="mappingtable",
                **common_params,
            )

    @mcp.tool()
    async def get_mappingtable(mappingtable_id: str) -> dict:
        """Get detailed metadata for a specific mapping table by its ID.

        Returns the full mapping table record including its name, description, version,
        publisher, source codelist URI, target codelist URI, registration status,
        validity period, and responsible persons.

        Args:
            mappingtable_id: The unique identifier (UUID) of the mapping table.

        Returns:
            JSON string with full mapping table metadata.
        """
        async with I14YApiClient() as client:
            return await client.get(
                f"/mappingtables/{mappingtable_id}",
                resource_type="mappingtable",
            )

    @mcp.tool()
    async def get_mappingtable_relations(
        mappingtable_id: str,
        format: str = "Json",
    ) -> dict:
        """Export all mapping relations (value correspondences) for a mapping table.

        Each relation pairs a value from the source codelist with its equivalent in the
        target codelist. Use this to retrieve the complete mapping, e.g. all old code →
        new code pairs.

        Args:
            mappingtable_id: The unique identifier (UUID) of the mapping table.
            format: Export format — "Json" (default) or "Csv".

        Returns:
            Mapping relations as a JSON array or CSV text.
        """
        valid = {"Json", "Csv"}
        if format not in valid:
            return {"error": f"Invalid format '{format}'", "valid_values": sorted(valid)}

        async with I14YApiClient() as client:
            return await client.get(f"/mappingtables/{mappingtable_id}/relations/exports/{format}")
