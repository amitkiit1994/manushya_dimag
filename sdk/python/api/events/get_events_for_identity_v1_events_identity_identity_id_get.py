from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.event_response import EventResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    identity_id: UUID,
    *,
    event_types: None | Unset | list[str] = UNSET,
    limit: Unset | int = 100,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_event_types: None | Unset | list[str]
    if isinstance(event_types, Unset):
        json_event_types = UNSET
    elif isinstance(event_types, list):
        json_event_types = event_types

    else:
        json_event_types = event_types
    params["event_types"] = json_event_types

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/events/identity/{identity_id}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list["EventResponse"] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = EventResponse.from_dict(response_200_item_data)

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
) -> Response[HTTPValidationError | list["EventResponse"]]:
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
    event_types: None | Unset | list[str] = UNSET,
    limit: Unset | int = 100,
) -> Response[HTTPValidationError | list["EventResponse"]]:
    """Get Events For Identity

     Get events for a specific identity.

    Args:
        identity_id (UUID):
        event_types (Union[None, Unset, list[str]]): Filter by event types
        limit (Union[Unset, int]): Maximum number of events to return Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['EventResponse']]]
    """

    kwargs = _get_kwargs(
        identity_id=identity_id,
        event_types=event_types,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    identity_id: UUID,
    *,
    client: AuthenticatedClient,
    event_types: None | Unset | list[str] = UNSET,
    limit: Unset | int = 100,
) -> HTTPValidationError | list["EventResponse"] | None:
    """Get Events For Identity

     Get events for a specific identity.

    Args:
        identity_id (UUID):
        event_types (Union[None, Unset, list[str]]): Filter by event types
        limit (Union[Unset, int]): Maximum number of events to return Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['EventResponse']]
    """

    return sync_detailed(
        identity_id=identity_id,
        client=client,
        event_types=event_types,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    identity_id: UUID,
    *,
    client: AuthenticatedClient,
    event_types: None | Unset | list[str] = UNSET,
    limit: Unset | int = 100,
) -> Response[HTTPValidationError | list["EventResponse"]]:
    """Get Events For Identity

     Get events for a specific identity.

    Args:
        identity_id (UUID):
        event_types (Union[None, Unset, list[str]]): Filter by event types
        limit (Union[Unset, int]): Maximum number of events to return Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['EventResponse']]]
    """

    kwargs = _get_kwargs(
        identity_id=identity_id,
        event_types=event_types,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    identity_id: UUID,
    *,
    client: AuthenticatedClient,
    event_types: None | Unset | list[str] = UNSET,
    limit: Unset | int = 100,
) -> HTTPValidationError | list["EventResponse"] | None:
    """Get Events For Identity

     Get events for a specific identity.

    Args:
        identity_id (UUID):
        event_types (Union[None, Unset, list[str]]): Filter by event types
        limit (Union[Unset, int]): Maximum number of events to return Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['EventResponse']]
    """

    return (
        await asyncio_detailed(
            identity_id=identity_id,
            client=client,
            event_types=event_types,
            limit=limit,
        )
    ).parsed
