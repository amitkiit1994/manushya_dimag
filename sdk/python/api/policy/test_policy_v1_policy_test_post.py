from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.test_policy_v1_policy_test_post_context import (
    TestPolicyV1PolicyTestPostContext,
)
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: TestPolicyV1PolicyTestPostContext,
    role: str,
    action: str,
    resource: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["role"] = role

    params["action"] = action

    params["resource"] = resource

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/policy/test",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
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
    body: TestPolicyV1PolicyTestPostContext,
    role: str,
    action: str,
    resource: str,
) -> Response[Any | HTTPValidationError]:
    """Test Policy

     Test a policy evaluation.

    Args:
        role (str):
        action (str):
        resource (str):
        body (TestPolicyV1PolicyTestPostContext):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
        role=role,
        action=action,
        resource=resource,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: TestPolicyV1PolicyTestPostContext,
    role: str,
    action: str,
    resource: str,
) -> Any | HTTPValidationError | None:
    """Test Policy

     Test a policy evaluation.

    Args:
        role (str):
        action (str):
        resource (str):
        body (TestPolicyV1PolicyTestPostContext):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        body=body,
        role=role,
        action=action,
        resource=resource,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: TestPolicyV1PolicyTestPostContext,
    role: str,
    action: str,
    resource: str,
) -> Response[Any | HTTPValidationError]:
    """Test Policy

     Test a policy evaluation.

    Args:
        role (str):
        action (str):
        resource (str):
        body (TestPolicyV1PolicyTestPostContext):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
        role=role,
        action=action,
        resource=resource,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: TestPolicyV1PolicyTestPostContext,
    role: str,
    action: str,
    resource: str,
) -> Any | HTTPValidationError | None:
    """Test Policy

     Test a policy evaluation.

    Args:
        role (str):
        action (str):
        resource (str):
        body (TestPolicyV1PolicyTestPostContext):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            role=role,
            action=action,
            resource=resource,
        )
    ).parsed
