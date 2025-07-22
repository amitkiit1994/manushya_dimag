from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.memory_response import MemoryResponse
from ...models.memory_update import MemoryUpdate
from ...types import Response


def _get_kwargs(
    memory_id: UUID,
    *,
    body: MemoryUpdate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/v1/memory/{memory_id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | MemoryResponse | None:
    if response.status_code == 200:
        response_200 = MemoryResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | MemoryResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    memory_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MemoryUpdate,
) -> Response[HTTPValidationError | MemoryResponse]:
    """Update Memory

     Update memory.

    Args:
        memory_id (UUID):
        body (MemoryUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, MemoryResponse]]
    """

    kwargs = _get_kwargs(
        memory_id=memory_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    memory_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MemoryUpdate,
) -> HTTPValidationError | MemoryResponse | None:
    """Update Memory

     Update memory.

    Args:
        memory_id (UUID):
        body (MemoryUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, MemoryResponse]
    """

    return sync_detailed(
        memory_id=memory_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    memory_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MemoryUpdate,
) -> Response[HTTPValidationError | MemoryResponse]:
    """Update Memory

     Update memory.

    Args:
        memory_id (UUID):
        body (MemoryUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, MemoryResponse]]
    """

    kwargs = _get_kwargs(
        memory_id=memory_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    memory_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MemoryUpdate,
) -> HTTPValidationError | MemoryResponse | None:
    """Update Memory

     Update memory.

    Args:
        memory_id (UUID):
        body (MemoryUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, MemoryResponse]
    """

    return (
        await asyncio_detailed(
            memory_id=memory_id,
            client=client,
            body=body,
        )
    ).parsed
