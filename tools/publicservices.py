"""MCP tools for I14Y PublicServices."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient
from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_publicservices(
        publisher_identifier: str | None = None,
        registration_status: str | None = None,
        publication_level: str | None = None,
        access_rights: str | None = None,
        publicservice_identifier: str | None = None,
        page: int = 1,
        page_size: int = 25,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """List public services registered on the Swiss I14Y platform.

        Public services are administrative services offered by Swiss federal, cantonal,
        or communal bodies to citizens, businesses, or other organisations.

        Pagination:
            By default this returns one page and includes pagination metadata from
            the API response headers. If fetch_all=True, all available pages are
            fetched unless max_pages is set. Use fetch_all=True only when the user
            explicitly asks for all matching public services or a complete scan.

        Args:
            publisher_identifier: Filter by the publishing organisation's identifier.
            registration_status: One of Initial, Candidate, Recorded, Qualified,
                Standard, PreferredStandard, Superseded, Retired.
            publication_level: "Internal" or "Public".
            access_rights: Filter by access restriction code.
            publicservice_identifier: Filter by the public service's own identifier.
            page: Page number (starts at 1).
            page_size: Number of results per page (default 25).
            fetch_all: Fetch all pages instead of only one page.
            max_pages: Optional maximum number of pages to fetch when fetch_all=True.

        Returns:
            JSON string with public service results and pagination metadata.
        """
        common_params = dict(
            publisherIdentifier=publisher_identifier,
            registrationStatus=registration_status,
            publicationLevel=publication_level,
            accessRights=access_rights,
            publicserviceIdentifier=publicservice_identifier,
        )

        async with I14YApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    "/publicservices",
                    page_size=page_size,
                    max_pages=max_pages,
                    resource_type="publicservice",
                    **common_params,
                )

            return await client.get(
                "/publicservices",
                page=page,
                pageSize=page_size,
                resource_type="publicservice",
                **common_params,
            )

    @mcp.tool()
    async def get_publicservice(publicservice_id: str) -> dict:
        """Get detailed metadata for a specific public service by its ID.

        Args:
            publicservice_id: The unique identifier of the public service.

        Returns:
            JSON string with full public service metadata.
        """
        async with I14YApiClient() as client:
            return await client.get(
                f"/publicservices/{publicservice_id}",
                resource_type="publicservice",
            )

    @mcp.tool()
    async def get_publicservice_by_identifier(identifier: str) -> dict:
        """Get a public service by its human-readable identifier (not UUID).

        Args:
            identifier: The public service identifier string.

        Returns:
            JSON object with full public service metadata.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/PublicServices/by-identifier/{identifier}")

    @mcp.tool()
    async def get_publicservice_relations(publicservice_id: str) -> dict:
        """Get public services related to a given public service.

        Returns other public services that are semantically linked to this one
        (e.g. prerequisite services, related administrative procedures).

        Args:
            publicservice_id: The unique identifier (UUID) of the public service.

        Returns:
            JSON array of related public services.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/PublicServices/{publicservice_id}/relations")
