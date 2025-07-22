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
    from ..models.identity_create_claims import IdentityCreateClaims


T = TypeVar("T", bound="IdentityCreate")


@_attrs_define
class IdentityCreate:
    """
    Attributes:
        external_id (str): External identifier for the identity
        role (str): Role of the identity
        claims (Union[Unset, IdentityCreateClaims]): Additional claims
    """

    external_id: str
    role: str
    claims: Union[Unset, "IdentityCreateClaims"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        external_id = self.external_id

        role = self.role

        claims: Unset | dict[str, Any] = UNSET
        if not isinstance(self.claims, Unset):
            claims = self.claims.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "external_id": external_id,
                "role": role,
            }
        )
        if claims is not UNSET:
            field_dict["claims"] = claims

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.identity_create_claims import IdentityCreateClaims

        d = dict(src_dict)
        external_id = d.pop("external_id")

        role = d.pop("role")

        _claims = d.pop("claims", UNSET)
        claims: Unset | IdentityCreateClaims
        if isinstance(_claims, Unset):
            claims = UNSET
        else:
            claims = IdentityCreateClaims.from_dict(_claims)

        identity_create = cls(
            external_id=external_id,
            role=role,
            claims=claims,
        )

        identity_create.additional_properties = d
        return identity_create

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
