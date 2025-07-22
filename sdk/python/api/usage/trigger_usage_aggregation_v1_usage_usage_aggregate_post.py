import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    target_date: None | Unset | datetime.date = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_target_date: None | Unset | str
    if isinstance(target_date, Unset):
        json_target_date = UNSET
    elif isinstance(target_date, datetime.date):
        json_target_date = target_date.isoformat()
    else:
        json_target_date = target_date
    params["target_date"] = json_target_date

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/usage/usage/aggregate",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = response.json()
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
) -> Response[Any | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    target_date: None | Unset | datetime.date = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Trigger Usage Aggregation

     Trigger manual usage aggregation (admin only).

    Args:
        target_date (Union[None, Unset, datetime.date]): Target date for aggregation (defaults to
            today)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        target_date=target_date,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    target_date: None | Unset | datetime.date = UNSET,
) -> Any | HTTPValidationError | None:
    """Trigger Usage Aggregation

     Trigger manual usage aggregation (admin only).

    Args:
        target_date (Union[None, Unset, datetime.date]): Target date for aggregation (defaults to
            today)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        target_date=target_date,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    target_date: None | Unset | datetime.date = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Trigger Usage Aggregation

     Trigger manual usage aggregation (admin only).

    Args:
        target_date (Union[None, Unset, datetime.date]): Target date for aggregation (defaults to
            today)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        target_date=target_date,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    target_date: None | Unset | datetime.date = UNSET,
) -> Any | HTTPValidationError | None:
    """Trigger Usage Aggregation

     Trigger manual usage aggregation (admin only).

    Args:
        target_date (Union[None, Unset, datetime.date]): Target date for aggregation (defaults to
            today)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            target_date=target_date,
        )
    ).parsed
