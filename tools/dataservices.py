"""MCP tools for I14Y DataServices."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_dataservices(
        publisher_identifier: str | None = None,
        registration_status: str | None = None,
        publication_level: str | None = None,
        access_rights: str | None = None,
        dataservice_identifier: str | None = None,
        page: int = 1,
        page_size: int = 25,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """List data services (APIs) registered on the Swiss I14Y platform.

        Data services are electronic interfaces (APIs) that provide access to datasets
        or functionality published by Swiss federal and cantonal bodies.

        Pagination:
            By default this returns one page and includes pagination metadata from
            the API response headers. If fetch_all=True, all available pages are
            fetched unless max_pages is set. Use fetch_all=True only when the user
            explicitly asks for all matching data services or a complete scan.

        Args:
            publisher_identifier: Filter by the publishing organisation's identifier.
            registration_status: One of Initial, Candidate, Recorded, Qualified,
                Standard, PreferredStandard, Superseded, Retired.
            publication_level: "Internal" or "Public".
            access_rights: Filter by access restriction code.
            dataservice_identifier: Filter by the data service's own identifier.
            page: Page number (starts at 1).
            page_size: Number of results per page (default 25).
            fetch_all: Fetch all pages instead of only one page.
            max_pages: Optional maximum number of pages to fetch when fetch_all=True.

        Returns:
            JSON string with data service results and pagination metadata.
        """
        common_params = dict(
            publisherIdentifier=publisher_identifier,
            registrationStatus=registration_status,
            publicationLevel=publication_level,
            accessRights=access_rights,
            dataServiceIdentifier=dataservice_identifier,
        )

        async with I14YApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    "/dataservices",
                    page_size=page_size,
                    max_pages=max_pages,
                    resource_type="dataservice",
                    **common_params,
                )

            return await client.get(
                "/dataservices",
                page=page,
                pageSize=page_size,
                resource_type="dataservice",
                **common_params,
            )

    @mcp.tool()
    async def get_dataservice(dataservice_id: str) -> dict:
        """Get detailed metadata for a specific data service by its ID.

        Args:
            dataservice_id: The unique identifier of the data service.

        Returns:
            JSON string with full data service metadata (title, description, endpoint URL,
            publisher, themes, etc.).
        """
        async with I14YApiClient() as client:
            return await client.get(
                f"/dataservices/{dataservice_id}",
                resource_type="dataservice",
            )

    @mcp.tool()
    async def get_dataservice_by_identifier(identifier: str) -> dict:
        """Get a data service by its human-readable identifier (not UUID).

        Args:
            identifier: The data service identifier string.

        Returns:
            JSON object with full data service metadata.
        """
        async with I14YApiClient() as client:
            response = await client.get(
                "/dataservices",
                resource_type="dataservice",
                dataServiceIdentifier=identifier,
                page=1,
                pageSize=1,
            )

            data = response.get("data") if isinstance(response, dict) else None
            if isinstance(data, list):
                if data:
                    return data[0]
                return {"error": f"Data service not found for identifier '{identifier}'"}

            return response
