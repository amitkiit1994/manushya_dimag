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
    *,
    event_type: None | Unset | str = UNSET,
    identity_id: None | UUID | Unset = UNSET,
    is_delivered: None | Unset | bool = UNSET,
    limit: Unset | int = 100,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_event_type: None | Unset | str
    if isinstance(event_type, Unset):
        json_event_type = UNSET
    else:
        json_event_type = event_type
    params["event_type"] = json_event_type

    json_identity_id: None | Unset | str
    if isinstance(identity_id, Unset):
        json_identity_id = UNSET
    elif isinstance(identity_id, UUID):
        json_identity_id = str(identity_id)
    else:
        json_identity_id = identity_id
    params["identity_id"] = json_identity_id

    json_is_delivered: None | Unset | bool
    if isinstance(is_delivered, Unset):
        json_is_delivered = UNSET
    else:
        json_is_delivered = is_delivered
    params["is_delivered"] = json_is_delivered

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/events/",
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
    *,
    client: AuthenticatedClient,
    event_type: None | Unset | str = UNSET,
    identity_id: None | UUID | Unset = UNSET,
    is_delivered: None | Unset | bool = UNSET,
    limit: Unset | int = 100,
) -> Response[HTTPValidationError | list["EventResponse"]]:
    """List Events

     List identity events with optional filtering.

    Args:
        event_type (Union[None, Unset, str]): Filter by event type
        identity_id (Union[None, UUID, Unset]): Filter by identity ID
        is_delivered (Union[None, Unset, bool]): Filter by delivery status
        limit (Union[Unset, int]): Maximum number of events to return Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['EventResponse']]]
    """

    kwargs = _get_kwargs(
        event_type=event_type,
        identity_id=identity_id,
        is_delivered=is_delivered,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    event_type: None | Unset | str = UNSET,
    identity_id: None | UUID | Unset = UNSET,
    is_delivered: None | Unset | bool = UNSET,
    limit: Unset | int = 100,
) -> HTTPValidationError | list["EventResponse"] | None:
    """List Events

     List identity events with optional filtering.

    Args:
        event_type (Union[None, Unset, str]): Filter by event type
        identity_id (Union[None, UUID, Unset]): Filter by identity ID
        is_delivered (Union[None, Unset, bool]): Filter by delivery status
        limit (Union[Unset, int]): Maximum number of events to return Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['EventResponse']]
    """

    return sync_detailed(
        client=client,
        event_type=event_type,
        identity_id=identity_id,
        is_delivered=is_delivered,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    event_type: None | Unset | str = UNSET,
    identity_id: None | UUID | Unset = UNSET,
    is_delivered: None | Unset | bool = UNSET,
    limit: Unset | int = 100,
) -> Response[HTTPValidationError | list["EventResponse"]]:
    """List Events

     List identity events with optional filtering.

    Args:
        event_type (Union[None, Unset, str]): Filter by event type
        identity_id (Union[None, UUID, Unset]): Filter by identity ID
        is_delivered (Union[None, Unset, bool]): Filter by delivery status
        limit (Union[Unset, int]): Maximum number of events to return Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['EventResponse']]]
    """

    kwargs = _get_kwargs(
        event_type=event_type,
        identity_id=identity_id,
        is_delivered=is_delivered,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    event_type: None | Unset | str = UNSET,
    identity_id: None | UUID | Unset = UNSET,
    is_delivered: None | Unset | bool = UNSET,
    limit: Unset | int = 100,
) -> HTTPValidationError | list["EventResponse"] | None:
    """List Events

     List identity events with optional filtering.

    Args:
        event_type (Union[None, Unset, str]): Filter by event type
        identity_id (Union[None, UUID, Unset]): Filter by identity ID
        is_delivered (Union[None, Unset, bool]): Filter by delivery status
        limit (Union[Unset, int]): Maximum number of events to return Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['EventResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            event_type=event_type,
            identity_id=identity_id,
            is_delivered=is_delivered,
            limit=limit,
        )
    ).parsed
