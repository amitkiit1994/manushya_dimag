from http import HTTPStatus
from typing import Any, cast
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    memory_id: UUID,
    *,
    hard_delete: Unset | bool = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["hard_delete"] = hard_delete

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/v1/memory/{memory_id}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | HTTPValidationError]:
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
    hard_delete: Unset | bool = False,
) -> Response[Any | HTTPValidationError]:
    """Delete Memory

     Delete memory (soft delete by default).

    Args:
        memory_id (UUID):
        hard_delete (Union[Unset, bool]): Perform hard delete Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        memory_id=memory_id,
        hard_delete=hard_delete,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    memory_id: UUID,
    *,
    client: AuthenticatedClient,
    hard_delete: Unset | bool = False,
) -> Any | HTTPValidationError | None:
    """Delete Memory

     Delete memory (soft delete by default).

    Args:
        memory_id (UUID):
        hard_delete (Union[Unset, bool]): Perform hard delete Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return sync_detailed(
        memory_id=memory_id,
        client=client,
        hard_delete=hard_delete,
    ).parsed


async def asyncio_detailed(
    memory_id: UUID,
    *,
    client: AuthenticatedClient,
    hard_delete: Unset | bool = False,
) -> Response[Any | HTTPValidationError]:
    """Delete Memory

     Delete memory (soft delete by default).

    Args:
        memory_id (UUID):
        hard_delete (Union[Unset, bool]): Perform hard delete Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        memory_id=memory_id,
        hard_delete=hard_delete,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    memory_id: UUID,
    *,
    client: AuthenticatedClient,
    hard_delete: Unset | bool = False,
) -> Any | HTTPValidationError | None:
    """Delete Memory

     Delete memory (soft delete by default).

    Args:
        memory_id (UUID):
        hard_delete (Union[Unset, bool]): Perform hard delete Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            memory_id=memory_id,
            client=client,
            hard_delete=hard_delete,
        )
    ).parsed
