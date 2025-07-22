from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.audit_trail_response import AuditTrailResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    event_type: None | Unset | str = UNSET,
    actor_id: None | Unset | str = UNSET,
    resource_type: None | Unset | str = UNSET,
    days: Unset | int = 7,
    limit: Unset | int = 100,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_event_type: None | Unset | str
    if isinstance(event_type, Unset):
        json_event_type = UNSET
    else:
        json_event_type = event_type
    params["event_type"] = json_event_type

    json_actor_id: None | Unset | str
    if isinstance(actor_id, Unset):
        json_actor_id = UNSET
    else:
        json_actor_id = actor_id
    params["actor_id"] = json_actor_id

    json_resource_type: None | Unset | str
    if isinstance(resource_type, Unset):
        json_resource_type = UNSET
    else:
        json_resource_type = resource_type
    params["resource_type"] = json_resource_type

    params["days"] = days

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/monitoring/audit-trail",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list["AuditTrailResponse"] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = AuditTrailResponse.from_dict(response_200_item_data)

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
) -> Response[HTTPValidationError | list["AuditTrailResponse"]]:
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
    actor_id: None | Unset | str = UNSET,
    resource_type: None | Unset | str = UNSET,
    days: Unset | int = 7,
    limit: Unset | int = 100,
) -> Response[HTTPValidationError | list["AuditTrailResponse"]]:
    """Get Audit Trail

     Get audit trail with filtering.

    Args:
        event_type (Union[None, Unset, str]): Filter by event type
        actor_id (Union[None, Unset, str]): Filter by actor ID
        resource_type (Union[None, Unset, str]): Filter by resource type
        days (Union[Unset, int]): Number of days to look back Default: 7.
        limit (Union[Unset, int]): Maximum number of records Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['AuditTrailResponse']]]
    """

    kwargs = _get_kwargs(
        event_type=event_type,
        actor_id=actor_id,
        resource_type=resource_type,
        days=days,
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
    actor_id: None | Unset | str = UNSET,
    resource_type: None | Unset | str = UNSET,
    days: Unset | int = 7,
    limit: Unset | int = 100,
) -> HTTPValidationError | list["AuditTrailResponse"] | None:
    """Get Audit Trail

     Get audit trail with filtering.

    Args:
        event_type (Union[None, Unset, str]): Filter by event type
        actor_id (Union[None, Unset, str]): Filter by actor ID
        resource_type (Union[None, Unset, str]): Filter by resource type
        days (Union[Unset, int]): Number of days to look back Default: 7.
        limit (Union[Unset, int]): Maximum number of records Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['AuditTrailResponse']]
    """

    return sync_detailed(
        client=client,
        event_type=event_type,
        actor_id=actor_id,
        resource_type=resource_type,
        days=days,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    event_type: None | Unset | str = UNSET,
    actor_id: None | Unset | str = UNSET,
    resource_type: None | Unset | str = UNSET,
    days: Unset | int = 7,
    limit: Unset | int = 100,
) -> Response[HTTPValidationError | list["AuditTrailResponse"]]:
    """Get Audit Trail

     Get audit trail with filtering.

    Args:
        event_type (Union[None, Unset, str]): Filter by event type
        actor_id (Union[None, Unset, str]): Filter by actor ID
        resource_type (Union[None, Unset, str]): Filter by resource type
        days (Union[Unset, int]): Number of days to look back Default: 7.
        limit (Union[Unset, int]): Maximum number of records Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['AuditTrailResponse']]]
    """

    kwargs = _get_kwargs(
        event_type=event_type,
        actor_id=actor_id,
        resource_type=resource_type,
        days=days,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    event_type: None | Unset | str = UNSET,
    actor_id: None | Unset | str = UNSET,
    resource_type: None | Unset | str = UNSET,
    days: Unset | int = 7,
    limit: Unset | int = 100,
) -> HTTPValidationError | list["AuditTrailResponse"] | None:
    """Get Audit Trail

     Get audit trail with filtering.

    Args:
        event_type (Union[None, Unset, str]): Filter by event type
        actor_id (Union[None, Unset, str]): Filter by actor ID
        resource_type (Union[None, Unset, str]): Filter by resource type
        days (Union[Unset, int]): Number of days to look back Default: 7.
        limit (Union[Unset, int]): Maximum number of records Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['AuditTrailResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            event_type=event_type,
            actor_id=actor_id,
            resource_type=resource_type,
            days=days,
            limit=limit,
        )
    ).parsed
