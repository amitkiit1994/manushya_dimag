from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.invitation_accept import InvitationAccept
from ...models.invitation_accept_response import InvitationAcceptResponse
from ...types import Response


def _get_kwargs(
    token: str,
    *,
    body: InvitationAccept,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/v1/invitations/accept/{token}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | InvitationAcceptResponse | None:
    if response.status_code == 200:
        response_200 = InvitationAcceptResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | InvitationAcceptResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    token: str,
    *,
    client: AuthenticatedClient | Client,
    body: InvitationAccept,
) -> Response[HTTPValidationError | InvitationAcceptResponse]:
    """Accept Invitation

     Accept an invitation and create identity.

    Args:
        token (str):
        body (InvitationAccept):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, InvitationAcceptResponse]]
    """

    kwargs = _get_kwargs(
        token=token,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    token: str,
    *,
    client: AuthenticatedClient | Client,
    body: InvitationAccept,
) -> HTTPValidationError | InvitationAcceptResponse | None:
    """Accept Invitation

     Accept an invitation and create identity.

    Args:
        token (str):
        body (InvitationAccept):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, InvitationAcceptResponse]
    """

    return sync_detailed(
        token=token,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    token: str,
    *,
    client: AuthenticatedClient | Client,
    body: InvitationAccept,
) -> Response[HTTPValidationError | InvitationAcceptResponse]:
    """Accept Invitation

     Accept an invitation and create identity.

    Args:
        token (str):
        body (InvitationAccept):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, InvitationAcceptResponse]]
    """

    kwargs = _get_kwargs(
        token=token,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    token: str,
    *,
    client: AuthenticatedClient | Client,
    body: InvitationAccept,
) -> HTTPValidationError | InvitationAcceptResponse | None:
    """Accept Invitation

     Accept an invitation and create identity.

    Args:
        token (str):
        body (InvitationAccept):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, InvitationAcceptResponse]
    """

    return (
        await asyncio_detailed(
            token=token,
            client=client,
            body=body,
        )
    ).parsed
