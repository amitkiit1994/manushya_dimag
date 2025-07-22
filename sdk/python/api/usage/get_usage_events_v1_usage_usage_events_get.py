import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.usage_event_response import UsageEventResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    start_date: None | Unset | datetime.date = UNSET,
    end_date: None | Unset | datetime.date = UNSET,
    event_type: None | Unset | str = UNSET,
    limit: Unset | int = 100,
    offset: Unset | int = 0,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_start_date: None | Unset | str
    if isinstance(start_date, Unset):
        json_start_date = UNSET
    elif isinstance(start_date, datetime.date):
        json_start_date = start_date.isoformat()
    else:
        json_start_date = start_date
    params["start_date"] = json_start_date

    json_end_date: None | Unset | str
    if isinstance(end_date, Unset):
        json_end_date = UNSET
    elif isinstance(end_date, datetime.date):
        json_end_date = end_date.isoformat()
    else:
        json_end_date = end_date
    params["end_date"] = json_end_date

    json_event_type: None | Unset | str
    if isinstance(event_type, Unset):
        json_event_type = UNSET
    else:
        json_event_type = event_type
    params["event_type"] = json_event_type

    params["limit"] = limit

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/usage/usage/events",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list["UsageEventResponse"] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = UsageEventResponse.from_dict(response_200_item_data)

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
) -> Response[HTTPValidationError | list["UsageEventResponse"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    start_date: None | Unset | datetime.date = UNSET,
    end_date: None | Unset | datetime.date = UNSET,
    event_type: None | Unset | str = UNSET,
    limit: Unset | int = 100,
    offset: Unset | int = 0,
) -> Response[HTTPValidationError | list["UsageEventResponse"]]:
    """Get Usage Events

     Get usage events for the current tenant.

    Args:
        start_date (Union[None, Unset, datetime.date]): Start date for filtering
        end_date (Union[None, Unset, datetime.date]): End date for filtering
        event_type (Union[None, Unset, str]): Filter by event type
        limit (Union[Unset, int]): Number of events to return Default: 100.
        offset (Union[Unset, int]): Number of events to skip Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['UsageEventResponse']]]
    """

    kwargs = _get_kwargs(
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    start_date: None | Unset | datetime.date = UNSET,
    end_date: None | Unset | datetime.date = UNSET,
    event_type: None | Unset | str = UNSET,
    limit: Unset | int = 100,
    offset: Unset | int = 0,
) -> HTTPValidationError | list["UsageEventResponse"] | None:
    """Get Usage Events

     Get usage events for the current tenant.

    Args:
        start_date (Union[None, Unset, datetime.date]): Start date for filtering
        end_date (Union[None, Unset, datetime.date]): End date for filtering
        event_type (Union[None, Unset, str]): Filter by event type
        limit (Union[Unset, int]): Number of events to return Default: 100.
        offset (Union[Unset, int]): Number of events to skip Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['UsageEventResponse']]
    """

    return sync_detailed(
        client=client,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        limit=limit,
        offset=offset,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    start_date: None | Unset | datetime.date = UNSET,
    end_date: None | Unset | datetime.date = UNSET,
    event_type: None | Unset | str = UNSET,
    limit: Unset | int = 100,
    offset: Unset | int = 0,
) -> Response[HTTPValidationError | list["UsageEventResponse"]]:
    """Get Usage Events

     Get usage events for the current tenant.

    Args:
        start_date (Union[None, Unset, datetime.date]): Start date for filtering
        end_date (Union[None, Unset, datetime.date]): End date for filtering
        event_type (Union[None, Unset, str]): Filter by event type
        limit (Union[Unset, int]): Number of events to return Default: 100.
        offset (Union[Unset, int]): Number of events to skip Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['UsageEventResponse']]]
    """

    kwargs = _get_kwargs(
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    start_date: None | Unset | datetime.date = UNSET,
    end_date: None | Unset | datetime.date = UNSET,
    event_type: None | Unset | str = UNSET,
    limit: Unset | int = 100,
    offset: Unset | int = 0,
) -> HTTPValidationError | list["UsageEventResponse"] | None:
    """Get Usage Events

     Get usage events for the current tenant.

    Args:
        start_date (Union[None, Unset, datetime.date]): Start date for filtering
        end_date (Union[None, Unset, datetime.date]): End date for filtering
        event_type (Union[None, Unset, str]): Filter by event type
        limit (Union[Unset, int]): Number of events to return Default: 100.
        offset (Union[Unset, int]): Number of events to skip Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['UsageEventResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            limit=limit,
            offset=offset,
        )
    ).parsed
