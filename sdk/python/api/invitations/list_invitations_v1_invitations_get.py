from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.invitation_response import InvitationResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    include_accepted: Unset | bool = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["include_accepted"] = include_accepted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/invitations/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list["InvitationResponse"] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = InvitationResponse.from_dict(response_200_item_data)

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
) -> Response[HTTPValidationError | list["InvitationResponse"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    include_accepted: Unset | bool = False,
) -> Response[HTTPValidationError | list["InvitationResponse"]]:
    """List Invitations

     List invitations.

    Args:
        include_accepted (Union[Unset, bool]): Include accepted invitations Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['InvitationResponse']]]
    """

    kwargs = _get_kwargs(
        include_accepted=include_accepted,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    include_accepted: Unset | bool = False,
) -> HTTPValidationError | list["InvitationResponse"] | None:
    """List Invitations

     List invitations.

    Args:
        include_accepted (Union[Unset, bool]): Include accepted invitations Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['InvitationResponse']]
    """

    return sync_detailed(
        client=client,
        include_accepted=include_accepted,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    include_accepted: Unset | bool = False,
) -> Response[HTTPValidationError | list["InvitationResponse"]]:
    """List Invitations

     List invitations.

    Args:
        include_accepted (Union[Unset, bool]): Include accepted invitations Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['InvitationResponse']]]
    """

    kwargs = _get_kwargs(
        include_accepted=include_accepted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    include_accepted: Unset | bool = False,
) -> HTTPValidationError | list["InvitationResponse"] | None:
    """List Invitations

     List invitations.

    Args:
        include_accepted (Union[Unset, bool]): Include accepted invitations Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['InvitationResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            include_accepted=include_accepted,
        )
    ).parsed
