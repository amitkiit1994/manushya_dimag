from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.webhook_delivery_response import WebhookDeliveryResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    webhook_id: UUID,
    *,
    status_filter: None | Unset | str = UNSET,
    limit: Unset | int = 50,
    offset: Unset | int = 0,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_status_filter: None | Unset | str
    if isinstance(status_filter, Unset):
        json_status_filter = UNSET
    else:
        json_status_filter = status_filter
    params["status_filter"] = json_status_filter

    params["limit"] = limit

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/webhooks/{webhook_id}/deliveries",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list["WebhookDeliveryResponse"] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = WebhookDeliveryResponse.from_dict(
                response_200_item_data
            )

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
) -> Response[HTTPValidationError | list["WebhookDeliveryResponse"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    webhook_id: UUID,
    *,
    client: AuthenticatedClient,
    status_filter: None | Unset | str = UNSET,
    limit: Unset | int = 50,
    offset: Unset | int = 0,
) -> Response[HTTPValidationError | list["WebhookDeliveryResponse"]]:
    """List Webhook Deliveries

     List deliveries for a specific webhook.

    Args:
        webhook_id (UUID):
        status_filter (Union[None, Unset, str]):
        limit (Union[Unset, int]):  Default: 50.
        offset (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['WebhookDeliveryResponse']]]
    """

    kwargs = _get_kwargs(
        webhook_id=webhook_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    webhook_id: UUID,
    *,
    client: AuthenticatedClient,
    status_filter: None | Unset | str = UNSET,
    limit: Unset | int = 50,
    offset: Unset | int = 0,
) -> HTTPValidationError | list["WebhookDeliveryResponse"] | None:
    """List Webhook Deliveries

     List deliveries for a specific webhook.

    Args:
        webhook_id (UUID):
        status_filter (Union[None, Unset, str]):
        limit (Union[Unset, int]):  Default: 50.
        offset (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['WebhookDeliveryResponse']]
    """

    return sync_detailed(
        webhook_id=webhook_id,
        client=client,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    ).parsed


async def asyncio_detailed(
    webhook_id: UUID,
    *,
    client: AuthenticatedClient,
    status_filter: None | Unset | str = UNSET,
    limit: Unset | int = 50,
    offset: Unset | int = 0,
) -> Response[HTTPValidationError | list["WebhookDeliveryResponse"]]:
    """List Webhook Deliveries

     List deliveries for a specific webhook.

    Args:
        webhook_id (UUID):
        status_filter (Union[None, Unset, str]):
        limit (Union[Unset, int]):  Default: 50.
        offset (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['WebhookDeliveryResponse']]]
    """

    kwargs = _get_kwargs(
        webhook_id=webhook_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    webhook_id: UUID,
    *,
    client: AuthenticatedClient,
    status_filter: None | Unset | str = UNSET,
    limit: Unset | int = 50,
    offset: Unset | int = 0,
) -> HTTPValidationError | list["WebhookDeliveryResponse"] | None:
    """List Webhook Deliveries

     List deliveries for a specific webhook.

    Args:
        webhook_id (UUID):
        status_filter (Union[None, Unset, str]):
        limit (Union[Unset, int]):  Default: 50.
        offset (Union[Unset, int]):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['WebhookDeliveryResponse']]
    """

    return (
        await asyncio_detailed(
            webhook_id=webhook_id,
            client=client,
            status_filter=status_filter,
            limit=limit,
            offset=offset,
        )
    ).parsed
