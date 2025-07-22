from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_key_response import ApiKeyResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    api_key_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/api-keys/{api_key_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiKeyResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ApiKeyResponse.from_dict(response.json())

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiKeyResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    api_key_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[ApiKeyResponse | HTTPValidationError]:
    """Get Api Key

     Get API key by ID.

    Args:
        api_key_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ApiKeyResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        api_key_id=api_key_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    api_key_id: UUID,
    *,
    client: AuthenticatedClient,
) -> ApiKeyResponse | HTTPValidationError | None:
    """Get Api Key

     Get API key by ID.

    Args:
        api_key_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ApiKeyResponse, HTTPValidationError]
    """

    return sync_detailed(
        api_key_id=api_key_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    api_key_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[ApiKeyResponse | HTTPValidationError]:
    """Get Api Key

     Get API key by ID.

    Args:
        api_key_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ApiKeyResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        api_key_id=api_key_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    api_key_id: UUID,
    *,
    client: AuthenticatedClient,
) -> ApiKeyResponse | HTTPValidationError | None:
    """Get Api Key

     Get API key by ID.

    Args:
        api_key_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ApiKeyResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            api_key_id=api_key_id,
            client=client,
        )
    ).parsed
