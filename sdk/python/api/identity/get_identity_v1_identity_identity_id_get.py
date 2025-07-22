from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.identity_response import IdentityResponse
from ...types import Response


def _get_kwargs(
    identity_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/identity/{identity_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | IdentityResponse | None:
    if response.status_code == 200:
        response_200 = IdentityResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | IdentityResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    identity_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | IdentityResponse]:
    """Get Identity

     Get identity by ID (requires appropriate permissions).
    Only for current tenant unless global/system-level.

    Args:
        identity_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, IdentityResponse]]
    """

    kwargs = _get_kwargs(
        identity_id=identity_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    identity_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | IdentityResponse | None:
    """Get Identity

     Get identity by ID (requires appropriate permissions).
    Only for current tenant unless global/system-level.

    Args:
        identity_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, IdentityResponse]
    """

    return sync_detailed(
        identity_id=identity_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    identity_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | IdentityResponse]:
    """Get Identity

     Get identity by ID (requires appropriate permissions).
    Only for current tenant unless global/system-level.

    Args:
        identity_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, IdentityResponse]]
    """

    kwargs = _get_kwargs(
        identity_id=identity_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    identity_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | IdentityResponse | None:
    """Get Identity

     Get identity by ID (requires appropriate permissions).
    Only for current tenant unless global/system-level.

    Args:
        identity_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, IdentityResponse]
    """

    return (
        await asyncio_detailed(
            identity_id=identity_id,
            client=client,
        )
    ).parsed
