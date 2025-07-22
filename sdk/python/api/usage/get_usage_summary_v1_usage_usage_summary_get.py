from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.usage_summary_response import UsageSummaryResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    days: Unset | int = 30,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["days"] = days

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/usage/usage/summary",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | UsageSummaryResponse | None:
    if response.status_code == 200:
        response_200 = UsageSummaryResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | UsageSummaryResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    days: Unset | int = 30,
) -> Response[HTTPValidationError | UsageSummaryResponse]:
    """Get Usage Summary

     Get usage summary for the current tenant.

    Args:
        days (Union[Unset, int]): Number of days to summarize Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, UsageSummaryResponse]]
    """

    kwargs = _get_kwargs(
        days=days,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    days: Unset | int = 30,
) -> HTTPValidationError | UsageSummaryResponse | None:
    """Get Usage Summary

     Get usage summary for the current tenant.

    Args:
        days (Union[Unset, int]): Number of days to summarize Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, UsageSummaryResponse]
    """

    return sync_detailed(
        client=client,
        days=days,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    days: Unset | int = 30,
) -> Response[HTTPValidationError | UsageSummaryResponse]:
    """Get Usage Summary

     Get usage summary for the current tenant.

    Args:
        days (Union[Unset, int]): Number of days to summarize Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, UsageSummaryResponse]]
    """

    kwargs = _get_kwargs(
        days=days,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    days: Unset | int = 30,
) -> HTTPValidationError | UsageSummaryResponse | None:
    """Get Usage Summary

     Get usage summary for the current tenant.

    Args:
        days (Union[Unset, int]): Number of days to summarize Default: 30.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, UsageSummaryResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            days=days,
        )
    ).parsed
