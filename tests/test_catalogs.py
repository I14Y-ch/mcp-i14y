"""Unit tests for catalog tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_list_catalogs_uses_partner_endpoint():
    with patch("helpers.i14y_api_client.I14YApiClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"data": []}
        from mcp.server.fastmcp import FastMCP
        from tools.catalogs import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "list_catalogs")
        await tool.fn(page=2, page_size=10)

    mock_get.assert_called_once_with("/catalogs", page=2, pageSize=10)


@pytest.mark.asyncio
async def test_get_catalog_records_uses_partner_endpoint():
    with patch("helpers.i14y_api_client.I14YApiClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"data": []}
        from mcp.server.fastmcp import FastMCP
        from tools.catalogs import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "get_catalog_records")
        await tool.fn(catalog_id="cat-123", page=1, page_size=25)

    mock_get.assert_called_once_with("/catalogs/cat-123/records", page=1, pageSize=25)


@pytest.mark.asyncio
async def test_get_catalog_themes_uses_partner_endpoint():
    with patch("helpers.i14y_api_client.I14YApiClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"data": []}
        from mcp.server.fastmcp import FastMCP
        from tools.catalogs import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "get_catalog_themes")
        await tool.fn(catalog_id="cat-123", page=1, page_size=100)

    mock_get.assert_called_once_with("/catalogs/cat-123/themes", page=1, pageSize=100)


@pytest.mark.asyncio
async def test_list_catalogs_fetch_all_uses_partner_endpoint():
    with patch(
        "helpers.i14y_api_client.I14YApiClient.get_all_pages", new_callable=AsyncMock
    ) as mock_get_all:
        mock_get_all.return_value = {"data": []}
        from mcp.server.fastmcp import FastMCP
        from tools.catalogs import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "list_catalogs")
        await tool.fn(fetch_all=True, page_size=50, max_pages=2)

    mock_get_all.assert_called_once_with("/catalogs", page_size=50, max_pages=2)
