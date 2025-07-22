from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.webhook_response import WebhookResponse
from ...types import Response


def _get_kwargs(
    webhook_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/webhooks/{webhook_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | WebhookResponse | None:
    if response.status_code == 200:
        response_200 = WebhookResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | WebhookResponse]:
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
) -> Response[HTTPValidationError | WebhookResponse]:
    """Get Webhook

     Get a specific webhook by ID.

    Args:
        webhook_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, WebhookResponse]]
    """

    kwargs = _get_kwargs(
        webhook_id=webhook_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    webhook_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | WebhookResponse | None:
    """Get Webhook

     Get a specific webhook by ID.

    Args:
        webhook_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, WebhookResponse]
    """

    return sync_detailed(
        webhook_id=webhook_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    webhook_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | WebhookResponse]:
    """Get Webhook

     Get a specific webhook by ID.

    Args:
        webhook_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, WebhookResponse]]
    """

    kwargs = _get_kwargs(
        webhook_id=webhook_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    webhook_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | WebhookResponse | None:
    """Get Webhook

     Get a specific webhook by ID.

    Args:
        webhook_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, WebhookResponse]
    """

    return (
        await asyncio_detailed(
            webhook_id=webhook_id,
            client=client,
        )
    ).parsed
