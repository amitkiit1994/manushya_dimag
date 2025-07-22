import datetime
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
    start_date: None | Unset | datetime.date = UNSET,
    end_date: None | Unset | datetime.date = UNSET,
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

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/usage/usage/admin/all-tenants",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list["UsageSummaryResponse"] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = UsageSummaryResponse.from_dict(response_200_item_data)

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
) -> Response[HTTPValidationError | list["UsageSummaryResponse"]]:
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
) -> Response[HTTPValidationError | list["UsageSummaryResponse"]]:
    """Get All Tenants Usage

     Get usage summary for all tenants (admin only).

    Args:
        start_date (Union[None, Unset, datetime.date]): Start date for filtering
        end_date (Union[None, Unset, datetime.date]): End date for filtering

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['UsageSummaryResponse']]]
    """

    kwargs = _get_kwargs(
        start_date=start_date,
        end_date=end_date,
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
) -> HTTPValidationError | list["UsageSummaryResponse"] | None:
    """Get All Tenants Usage

     Get usage summary for all tenants (admin only).

    Args:
        start_date (Union[None, Unset, datetime.date]): Start date for filtering
        end_date (Union[None, Unset, datetime.date]): End date for filtering

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['UsageSummaryResponse']]
    """

    return sync_detailed(
        client=client,
        start_date=start_date,
        end_date=end_date,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    start_date: None | Unset | datetime.date = UNSET,
    end_date: None | Unset | datetime.date = UNSET,
) -> Response[HTTPValidationError | list["UsageSummaryResponse"]]:
    """Get All Tenants Usage

     Get usage summary for all tenants (admin only).

    Args:
        start_date (Union[None, Unset, datetime.date]): Start date for filtering
        end_date (Union[None, Unset, datetime.date]): End date for filtering

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['UsageSummaryResponse']]]
    """

    kwargs = _get_kwargs(
        start_date=start_date,
        end_date=end_date,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    start_date: None | Unset | datetime.date = UNSET,
    end_date: None | Unset | datetime.date = UNSET,
) -> HTTPValidationError | list["UsageSummaryResponse"] | None:
    """Get All Tenants Usage

     Get usage summary for all tenants (admin only).

    Args:
        start_date (Union[None, Unset, datetime.date]): Start date for filtering
        end_date (Union[None, Unset, datetime.date]): End date for filtering

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['UsageSummaryResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            start_date=start_date,
            end_date=end_date,
        )
    ).parsed
