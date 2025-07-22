from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.policy_response import PolicyResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    role: None | Unset | str = UNSET,
    is_active: None | Unset | bool = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

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
        "url": "/v1/policy/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list["PolicyResponse"] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = PolicyResponse.from_dict(response_200_item_data)

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
) -> Response[HTTPValidationError | list["PolicyResponse"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    role: None | Unset | str = UNSET,
    is_active: None | Unset | bool = UNSET,
) -> Response[HTTPValidationError | list["PolicyResponse"]]:
    """List Policies

     List policies.

    Args:
        role (Union[None, Unset, str]):
        is_active (Union[None, Unset, bool]): Filter by active/inactive policies. Default: only
            active.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['PolicyResponse']]]
    """

    kwargs = _get_kwargs(
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
    role: None | Unset | str = UNSET,
    is_active: None | Unset | bool = UNSET,
) -> HTTPValidationError | list["PolicyResponse"] | None:
    """List Policies

     List policies.

    Args:
        role (Union[None, Unset, str]):
        is_active (Union[None, Unset, bool]): Filter by active/inactive policies. Default: only
            active.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['PolicyResponse']]
    """

    return sync_detailed(
        client=client,
        role=role,
        is_active=is_active,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    role: None | Unset | str = UNSET,
    is_active: None | Unset | bool = UNSET,
) -> Response[HTTPValidationError | list["PolicyResponse"]]:
    """List Policies

     List policies.

    Args:
        role (Union[None, Unset, str]):
        is_active (Union[None, Unset, bool]): Filter by active/inactive policies. Default: only
            active.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['PolicyResponse']]]
    """

    kwargs = _get_kwargs(
        role=role,
        is_active=is_active,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    role: None | Unset | str = UNSET,
    is_active: None | Unset | bool = UNSET,
) -> HTTPValidationError | list["PolicyResponse"] | None:
    """List Policies

     List policies.

    Args:
        role (Union[None, Unset, str]):
        is_active (Union[None, Unset, bool]): Filter by active/inactive policies. Default: only
            active.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['PolicyResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            role=role,
            is_active=is_active,
        )
    ).parsed
