from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_key_response import ApiKeyResponse
from ...models.api_key_update import ApiKeyUpdate
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    api_key_id: UUID,
    *,
    body: ApiKeyUpdate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/v1/api-keys/{api_key_id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
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
    body: ApiKeyUpdate,
) -> Response[ApiKeyResponse | HTTPValidationError]:
    """Update Api Key

     Update API key.

    Args:
        api_key_id (UUID):
        body (ApiKeyUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ApiKeyResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        api_key_id=api_key_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    api_key_id: UUID,
    *,
    client: AuthenticatedClient,
    body: ApiKeyUpdate,
) -> ApiKeyResponse | HTTPValidationError | None:
    """Update Api Key

     Update API key.

    Args:
        api_key_id (UUID):
        body (ApiKeyUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ApiKeyResponse, HTTPValidationError]
    """

    return sync_detailed(
        api_key_id=api_key_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    api_key_id: UUID,
    *,
    client: AuthenticatedClient,
    body: ApiKeyUpdate,
) -> Response[ApiKeyResponse | HTTPValidationError]:
    """Update Api Key

     Update API key.

    Args:
        api_key_id (UUID):
        body (ApiKeyUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ApiKeyResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        api_key_id=api_key_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    api_key_id: UUID,
    *,
    client: AuthenticatedClient,
    body: ApiKeyUpdate,
) -> ApiKeyResponse | HTTPValidationError | None:
    """Update Api Key

     Update API key.

    Args:
        api_key_id (UUID):
        body (ApiKeyUpdate):

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
            body=body,
        )
    ).parsed
