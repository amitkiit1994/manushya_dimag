from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.identity_response import IdentityResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: Unset | int = 0,
    limit: Unset | int = 100,
    role: None | Unset | str = UNSET,
    is_active: None | Unset | bool = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    json_role: None | Unset | str
    if isinstance(role, Unset):
        json_role = UNSET
    else:
        json_role = role
    params["role"] = json_role

    json_is_active: None | Unset | bool
    if isinstance(is_active, Unset):
        json_is_active = UNSET
    else:
        json_is_active = is_active
    params["is_active"] = json_is_active

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/identity/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list["IdentityResponse"] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = IdentityResponse.from_dict(response_200_item_data)

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
) -> Response[HTTPValidationError | list["IdentityResponse"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    skip: Unset | int = 0,
    limit: Unset | int = 100,
    role: None | Unset | str = UNSET,
    is_active: None | Unset | bool = UNSET,
) -> Response[HTTPValidationError | list["IdentityResponse"]]:
    """List Identities

     List identities (requires appropriate permissions).
    By default, only active identities are returned.
    Use is_active=false to list inactive, or is_active=all to list all (admin only).
    Only returns identities for the current tenant,
    unless current identity is global/system-level.

    Args:
        skip (Union[Unset, int]):  Default: 0.
        limit (Union[Unset, int]):  Default: 100.
        role (Union[None, Unset, str]):
        is_active (Union[None, Unset, bool]): Filter by active/inactive identities. Default: only
            active.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['IdentityResponse']]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    skip: Unset | int = 0,
    limit: Unset | int = 100,
    role: None | Unset | str = UNSET,
    is_active: None | Unset | bool = UNSET,
) -> HTTPValidationError | list["IdentityResponse"] | None:
    """List Identities

     List identities (requires appropriate permissions).
    By default, only active identities are returned.
    Use is_active=false to list inactive, or is_active=all to list all (admin only).
    Only returns identities for the current tenant,
    unless current identity is global/system-level.

    Args:
        skip (Union[Unset, int]):  Default: 0.
        limit (Union[Unset, int]):  Default: 100.
        role (Union[None, Unset, str]):
        is_active (Union[None, Unset, bool]): Filter by active/inactive identities. Default: only
            active.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['IdentityResponse']]
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    skip: Unset | int = 0,
    limit: Unset | int = 100,
    role: None | Unset | str = UNSET,
    is_active: None | Unset | bool = UNSET,
) -> Response[HTTPValidationError | list["IdentityResponse"]]:
    """List Identities

     List identities (requires appropriate permissions).
    By default, only active identities are returned.
    Use is_active=false to list inactive, or is_active=all to list all (admin only).
    Only returns identities for the current tenant,
    unless current identity is global/system-level.

    Args:
        skip (Union[Unset, int]):  Default: 0.
        limit (Union[Unset, int]):  Default: 100.
        role (Union[None, Unset, str]):
        is_active (Union[None, Unset, bool]): Filter by active/inactive identities. Default: only
            active.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['IdentityResponse']]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    skip: Unset | int = 0,
    limit: Unset | int = 100,
    role: None | Unset | str = UNSET,
    is_active: None | Unset | bool = UNSET,
) -> HTTPValidationError | list["IdentityResponse"] | None:
    """List Identities

     List identities (requires appropriate permissions).
    By default, only active identities are returned.
    Use is_active=false to list inactive, or is_active=all to list all (admin only).
    Only returns identities for the current tenant,
    unless current identity is global/system-level.

    Args:
        skip (Union[Unset, int]):  Default: 0.
        limit (Union[Unset, int]):  Default: 100.
        role (Union[None, Unset, str]):
        is_active (Union[None, Unset, bool]): Filter by active/inactive identities. Default: only
            active.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['IdentityResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            role=role,
            is_active=is_active,
        )
    ).parsed
