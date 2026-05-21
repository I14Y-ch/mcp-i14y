"""MCP tools for I14Y controlled vocabularies.

Controlled vocabularies define the allowed values for RDF/DCAT-AP properties
such as themes, access rights, media types, licenses, and update frequencies.
They are used to ensure interoperability between I14Y and EU DCAT-AP metadata.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_vocabularies() -> dict:
        """List all controlled vocabularies available on the I14Y platform.

        Controlled vocabularies define valid values for DCAT-AP metadata fields.
        Common vocabularies include:

        - ``Concept_DATASET_THEME`` — EU Data Themes (DCAT dcat:theme)
        - ``RightsStatement_ACCESS_RIGHTS`` — Access rights codes (dcterms:accessRights)
        - ``VOCAB_EU_FREQUENCY`` — Update frequency (dcterms:accrualPeriodicity)
        - ``VOCAB_I14Y_LICENSE`` — License types (dcterms:license)
        - ``VOCAB_I14Y_MEDIA_TYPE`` — Media/MIME types (dcat:mediaType)

        Use get_vocabulary(identifier) to retrieve the entries of a specific vocabulary.

        Returns:
            JSON array of vocabulary configurations with vocabularyIdentifier,
            conceptIdentifier, and conceptVersion.
        """
        async with CoreApiClient() as client:
            return await client.get("/Vocabularies/configurations")

    @mcp.tool()
    async def get_vocabulary(identifier: str) -> dict:
        """Get all entries of a controlled vocabulary by its identifier.

        Use this to retrieve the valid values for a DCAT-AP metadata field.
        For example, call get_vocabulary("Concept_DATASET_THEME") to get the
        list of EU Data Theme URIs and labels for annotating datasets.

        Common vocabulary identifiers (from list_vocabularies()):
        - ``Concept_DATASET_THEME`` — EU Data Themes
        - ``RightsStatement_ACCESS_RIGHTS`` — Access rights
        - ``VOCAB_EU_FREQUENCY`` — Update frequencies
        - ``VOCAB_I14Y_LICENSE`` — Licenses
        - ``VOCAB_I14Y_MEDIA_TYPE`` — Media types
        - ``VOCAB_I14Y_PACKAGING_FORMAT`` — Packaging formats

        Args:
            identifier: The vocabulary identifier (e.g. "Concept_DATASET_THEME").

        Returns:
            JSON object with vocabulary entries including code, URI, and
            multilingual labels.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/Vocabularies/{identifier}")
