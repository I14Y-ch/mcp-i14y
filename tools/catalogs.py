"""MCP tools for I14Y Catalogs (DCAT-AP exports)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient
from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_catalog(
        catalog_id: str,
        format: str = "ttl",
    ) -> dict:
        """Export a catalog from the Swiss I14Y platform in DCAT-AP format.

        Catalogs aggregate datasets, data services, and other resources published by
        an organisation. The export is DCAT-AP (EU Application Profile for Data Catalogs)
        compliant.

        Args:
            catalog_id: The unique identifier of the catalog.
            format: Export format — "ttl" (Turtle, default) or "rdf" (RDF/XML).

        Returns:
            Catalog data as Turtle or RDF/XML text.
        """
        valid = {"ttl", "rdf"}
        if format not in valid:
            return {"error": f"Invalid format '{format}'", "valid_values": sorted(valid)}

        async with I14YApiClient() as client:
            return await client.get(f"/catalogs/{catalog_id}/dcat/exports/{format}")

    @mcp.tool()
    async def list_catalogs(
        page: int = 1,
        page_size: int = 25,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """List all DCAT catalogs registered on the I14Y platform.

        A catalog aggregates datasets, data services, and other resources published by
        an organisation. Use this to discover available catalogs before exporting one
        with get_catalog().

        Pagination:
            By default this returns one page and includes pagination metadata from
            the API response headers. If fetch_all=True, all available pages are
            fetched unless max_pages is set.

        Args:
            page: Page number (starts at 1).
            page_size: Results per page (default 25).
            fetch_all: Fetch all pages instead of only one page.
            max_pages: Optional maximum number of pages to fetch when fetch_all=True.

        Returns:
            JSON object with catalog results and pagination metadata.
        """
        async with CoreApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    "/DcatCatalogs",
                    page_size=page_size,
                    max_pages=max_pages,
                )

            return await client.get("/DcatCatalogs", page=page, pageSize=page_size)

    @mcp.tool()
    async def get_catalog_records(
        catalog_id: str,
        page: int = 1,
        page_size: int = 25,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """Get catalog records (resource entries) from a specific DCAT catalog.

        Catalog records link a catalog to the datasets and data services it contains,
        with provenance metadata (when the record was added, modified, etc.).

        Pagination:
            By default this returns one page and includes pagination metadata from
            the API response headers. If fetch_all=True, all available pages are
            fetched unless max_pages is set.

        Args:
            catalog_id: The unique identifier (UUID) of the catalog.
            page: Page number (starts at 1).
            page_size: Results per page (default 25).
            fetch_all: Fetch all pages instead of only one page.
            max_pages: Optional maximum number of pages to fetch when fetch_all=True.

        Returns:
            JSON object with catalog records and pagination metadata.
        """
        async with CoreApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    f"/DcatCatalogs/{catalog_id}/records",
                    page_size=page_size,
                    max_pages=max_pages,
                )

            return await client.get(
                f"/DcatCatalogs/{catalog_id}/records",
                page=page,
                pageSize=page_size,
            )

    @mcp.tool()
    async def get_catalog_themes(
        catalog_id: str,
        page: int = 1,
        page_size: int = 100,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """Get themes used within a specific DCAT catalog.

        Returns the controlled vocabulary themes (from the EU Data Theme vocabulary)
        assigned to resources in this catalog. Useful for understanding the thematic
        coverage of a catalog and for RDF/DCAT alignment.

        Pagination:
            By default this returns one page and includes pagination metadata from
            the API response headers. If fetch_all=True, all available pages are
            fetched unless max_pages is set.

        Args:
            catalog_id: The unique identifier (UUID) of the catalog.
            page: Page number (starts at 1).
            page_size: Results per page (default 100).
            fetch_all: Fetch all pages instead of only one page.
            max_pages: Optional maximum number of pages to fetch when fetch_all=True.

        Returns:
            JSON object with catalog themes and pagination metadata.
        """
        async with CoreApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    f"/DcatCatalogs/{catalog_id}/themes",
                    page_size=page_size,
                    max_pages=max_pages,
                )

            return await client.get(
                f"/DcatCatalogs/{catalog_id}/themes",
                page=page,
                pageSize=page_size,
            )
