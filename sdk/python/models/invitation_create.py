from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.invitation_create_claims import InvitationCreateClaims


T = TypeVar("T", bound="InvitationCreate")


@_attrs_define
class InvitationCreate:
    """
    Attributes:
        email (str): Email address to invite
        role (str): Role for the invited user
        claims (Union[Unset, InvitationCreateClaims]): Additional claims for the user
        expires_in_days (Union[Unset, int]): Invitation expiration in days Default: 7.
    """

    email: str
    role: str
    claims: Union[Unset, "InvitationCreateClaims"] = UNSET
    expires_in_days: Unset | int = 7
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        role = self.role

        claims: Unset | dict[str, Any] = UNSET
        if not isinstance(self.claims, Unset):
            claims = self.claims.to_dict()

        expires_in_days = self.expires_in_days

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "role": role,
            }
        )
        if claims is not UNSET:
            field_dict["claims"] = claims
        if expires_in_days is not UNSET:
            field_dict["expires_in_days"] = expires_in_days

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.invitation_create_claims import InvitationCreateClaims

        d = dict(src_dict)
        email = d.pop("email")

        role = d.pop("role")

        _claims = d.pop("claims", UNSET)
        claims: Unset | InvitationCreateClaims
        if isinstance(_claims, Unset):
            claims = UNSET
        else:
            claims = InvitationCreateClaims.from_dict(_claims)

        expires_in_days = d.pop("expires_in_days", UNSET)

        invitation_create = cls(
            email=email,
            role=role,
            claims=claims,
            expires_in_days=expires_in_days,
        )

        invitation_create.additional_properties = d
        return invitation_create

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
