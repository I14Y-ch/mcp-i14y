"""MCP tools for I14Y Agents (publishing organisations).

Agents are the organisations that publish datasets, data services, concepts, and other
resources on the I14Y platform. Knowing which agents are available helps filter resources
by publisher.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_agents(
        page: int = 1,
        page_size: int = 25,
        fetch_all: bool = False,
        max_pages: int | None = None,
    ) -> dict:
        """List all publishing organisations (agents) registered on I14Y.

        Agents are the federal offices, cantonal bodies, and other organisations
        that publish resources on the I14Y platform.

        Use this to discover available publisher identifiers for use in other tools'
        publisher_identifier filter.

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
            JSON object with agent results and pagination metadata.
        """
        async with CoreApiClient() as client:
            if fetch_all:
                return await client.get_all_pages(
                    "/Agents",
                    page_size=page_size,
                    max_pages=max_pages,
                )

            return await client.get("/Agents", page=page, pageSize=page_size)

    @mcp.tool()
    async def get_agent(agent_id: str) -> dict:
        """Get detailed metadata for a specific publishing organisation.

        Returns full agent record including name, description, contact point, homepage,
        spatial coverage, and sub-organisations.

        Args:
            agent_id: The unique identifier (UUID) of the agent.

        Returns:
            JSON object with full agent metadata.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/Agents/{agent_id}")
