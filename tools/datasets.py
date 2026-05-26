"""MCP tools for I14Y Datasets."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient
from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]

_STRUCTURE_FILTER_MAP = {
    True: "WithStructure",
    False: "WithoutStructure",
}


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_datasets(
        publisher_identifier: str | None = None,
        registration_status: str | None = None,
        publication_level: str | None = None,
        access_rights: str | None = None,
        dataset_identifier: str | None = None,
        with_structure: bool | None = None,
        page: int = 1,
        page_size: int = 25,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """List datasets from the Swiss I14Y interoperability platform.

        Supports filtering by publisher, registration status, publication level,
        access rights, and a specific dataset identifier.

        Note:
            The I14Y `/api/datasets` endpoint does not support a structure filter.
            When `with_structure` is provided, this tool automatically uses CORE
            `/Catalog/search` with `types=["Dataset"]` and `structure`
            (`WithStructure`/`WithoutStructure`).

        Pagination:
            By default this returns one page and includes pagination metadata from
            the API response headers. If fetch_all=True, all available pages are
            fetched unless max_pages is set. Use fetch_all=True only when the user
            explicitly asks for all matching datasets or a complete scan.

        Args:
            publisher_identifier: Filter by the publishing organisation's identifier.
            registration_status: One of Initial, Candidate, Recorded, Qualified,
                Standard, PreferredStandard, Superseded, Retired.
            publication_level: "Internal" or "Public".
            access_rights: Filter by access restriction code.
            dataset_identifier: Filter by the dataset's own identifier.
            with_structure: Filter by structure-model availability via CORE search.
            page: Page number (starts at 1).
            page_size: Number of results per page (default 25).
            fetch_all: Fetch all pages instead of only one page.
            max_pages: Optional maximum number of pages to fetch when fetch_all=True.

        Returns:
            JSON string with dataset results and pagination metadata.
        """
        common_params = dict(
            publisherIdentifier=publisher_identifier,
            registrationStatus=registration_status,
            publicationLevel=publication_level,
            accessRights=access_rights,
            datasetIdentifier=dataset_identifier,
        )

        if with_structure is not None:
            search_params = dict(
                query=dataset_identifier,
                types=["Dataset"],
                publishers=[publisher_identifier] if publisher_identifier else None,
                statuses=[registration_status] if registration_status else None,
                publicationLevels=[publication_level] if publication_level else None,
                accessRights=[access_rights] if access_rights else None,
                structure=_STRUCTURE_FILTER_MAP[with_structure],
            )

            async with CoreApiClient() as client:
                if fetch_all:
                    return await client.get_all_pages(
                        "/Catalog/search",
                        page_size=page_size,
                        max_pages=max_pages,
                        catalog_search=True,
                        **search_params,
                    )

                return await client.get(
                    "/Catalog/search",
                    catalog_search=True,
                    page=page,
                    pageSize=page_size,
                    **search_params,
                )

        async with I14YApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    "/datasets",
                    page_size=page_size,
                    max_pages=max_pages,
                    resource_type="dataset",
                    **common_params,
                )

            return await client.get(
                "/datasets",
                resource_type="dataset",
                page=page,
                pageSize=page_size,
                **common_params,
            )

    @mcp.tool()
    async def get_dataset(dataset_id: str) -> dict:
        """Get detailed metadata for a specific dataset by its ID.

        Args:
            dataset_id: The unique identifier of the dataset.

        Returns:
            JSON string with full dataset metadata (title, description, publisher,
            themes, distributions, etc.).
        """
        async with I14YApiClient() as client:
            return await client.get(f"/datasets/{dataset_id}", resource_type="dataset")

    @mcp.tool()
    async def get_dataset_structure(
        dataset_id: str,
        format: str = "JsonLd",
    ) -> dict:
        """Export the structural schema of a dataset.

        Args:
            dataset_id: The unique identifier of the dataset.
            format: Export format — "JsonLd" (default), "Ttl" (Turtle), or "Rdf" (RDF/XML).

        Returns:
            Dataset structure in the requested format.
        """
        valid = {"JsonLd", "Ttl", "Rdf"}
        if format not in valid:
            return {"error": f"Invalid format '{format}'", "valid_values": sorted(valid)}

        async with I14YApiClient() as client:
            return await client.get(f"/datasets/{dataset_id}/structures/exports/{format}")

    @mcp.tool()
    async def get_dataset_by_identifier(identifier: str) -> dict:
        """Get a dataset by its human-readable identifier (not UUID).

        Use this when you know the dataset's short identifier (e.g.
        "px-x-0602010000_109") rather than its UUID. More convenient than
        list_datasets() with a filter.

        Args:
            identifier: The dataset identifier string.

        Returns:
            JSON object with full dataset metadata.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/Datasets/by-identifier/{identifier}")

    @mcp.tool()
    async def check_dataset_has_structure(dataset_id: str) -> dict:
        """Check whether a dataset has a structural model defined on I14Y.

        Use this before calling get_dataset_structure() to avoid errors on datasets
        with no model. Useful for filtering a list of datasets to only those with
        documented schemas.

        Args:
            dataset_id: The unique identifier (UUID) of the dataset.

        Returns:
            JSON boolean — true if a structure model exists, false otherwise.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/Datasets/{dataset_id}/model/exists")
