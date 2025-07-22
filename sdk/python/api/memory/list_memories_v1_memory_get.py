from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.memory_response import MemoryResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: Unset | int = 0,
    limit: Unset | int = 100,
    memory_type: None | Unset | str = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    json_memory_type: None | Unset | str
    if isinstance(memory_type, Unset):
        json_memory_type = UNSET
    else:
        json_memory_type = memory_type
    params["memory_type"] = json_memory_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/memory/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list["MemoryResponse"] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = MemoryResponse.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list["MemoryResponse"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    skip: Unset | int = 0,
    limit: Unset | int = 100,
    memory_type: None | Unset | str = UNSET,
) -> Response[HTTPValidationError | list["MemoryResponse"]]:
    """List Memories

     List memories for current identity.

    Args:
        skip (Union[Unset, int]):  Default: 0.
        limit (Union[Unset, int]):  Default: 100.
        memory_type (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['MemoryResponse']]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        memory_type=memory_type,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    skip: Unset | int = 0,
    limit: Unset | int = 100,
    memory_type: None | Unset | str = UNSET,
) -> HTTPValidationError | list["MemoryResponse"] | None:
    """List Memories

     List memories for current identity.

    Args:
        skip (Union[Unset, int]):  Default: 0.
        limit (Union[Unset, int]):  Default: 100.
        memory_type (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['MemoryResponse']]
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        memory_type=memory_type,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    skip: Unset | int = 0,
    limit: Unset | int = 100,
    memory_type: None | Unset | str = UNSET,
) -> Response[HTTPValidationError | list["MemoryResponse"]]:
    """List Memories

     List memories for current identity.

    Args:
        skip (Union[Unset, int]):  Default: 0.
        limit (Union[Unset, int]):  Default: 100.
        memory_type (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['MemoryResponse']]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        memory_type=memory_type,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    skip: Unset | int = 0,
    limit: Unset | int = 100,
    memory_type: None | Unset | str = UNSET,
) -> HTTPValidationError | list["MemoryResponse"] | None:
    """List Memories

     List memories for current identity.

    Args:
        skip (Union[Unset, int]):  Default: 0.
        limit (Union[Unset, int]):  Default: 100.
        memory_type (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['MemoryResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            memory_type=memory_type,
        )
    ).parsed
