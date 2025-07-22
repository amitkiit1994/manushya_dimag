from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.invitation_accept_response_identity import (
        InvitationAcceptResponseIdentity,
    )


T = TypeVar("T", bound="InvitationAcceptResponse")


@_attrs_define
class InvitationAcceptResponse:
    """
    Attributes:
        identity (InvitationAcceptResponseIdentity):
        token (str): JWT token for the new identity
    """

    identity: "InvitationAcceptResponseIdentity"
    token: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        identity = self.identity.to_dict()

        token = self.token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "identity": identity,
                "token": token,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.invitation_accept_response_identity import (
            InvitationAcceptResponseIdentity,
        )

        d = dict(src_dict)
        identity = InvitationAcceptResponseIdentity.from_dict(d.pop("identity"))

        token = d.pop("token")

        invitation_accept_response = cls(
            identity=identity,
            token=token,
        )

        invitation_accept_response.additional_properties = d
        return invitation_accept_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
