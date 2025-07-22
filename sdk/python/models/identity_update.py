from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.identity_update_claims_type_0 import IdentityUpdateClaimsType0


T = TypeVar("T", bound="IdentityUpdate")


@_attrs_define
class IdentityUpdate:
    """
    Attributes:
        role (Union[None, Unset, str]): Role of the identity
        claims (Union['IdentityUpdateClaimsType0', None, Unset]): Additional claims
        is_active (Union[None, Unset, bool]): Whether the identity is active
    """

    role: None | Unset | str = UNSET
    claims: Union["IdentityUpdateClaimsType0", None, Unset] = UNSET
    is_active: None | Unset | bool = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.identity_update_claims_type_0 import IdentityUpdateClaimsType0

        role: None | Unset | str
        if isinstance(self.role, Unset):
            role = UNSET
        else:
            role = self.role

        claims: None | Unset | dict[str, Any]
        if isinstance(self.claims, Unset):
            claims = UNSET
        elif isinstance(self.claims, IdentityUpdateClaimsType0):
            claims = self.claims.to_dict()
        else:
            claims = self.claims

        is_active: None | Unset | bool
        if isinstance(self.is_active, Unset):
            is_active = UNSET
        else:
            is_active = self.is_active

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if role is not UNSET:
            field_dict["role"] = role
        if claims is not UNSET:
            field_dict["claims"] = claims
        if is_active is not UNSET:
            field_dict["is_active"] = is_active

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.identity_update_claims_type_0 import IdentityUpdateClaimsType0

        d = dict(src_dict)

        def _parse_role(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        role = _parse_role(d.pop("role", UNSET))

        def _parse_claims(
            data: object,
        ) -> Union["IdentityUpdateClaimsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                claims_type_0 = IdentityUpdateClaimsType0.from_dict(data)

                return claims_type_0
            except:  # noqa: E722
                pass
            return cast(Union["IdentityUpdateClaimsType0", None, Unset], data)

        claims = _parse_claims(d.pop("claims", UNSET))

        def _parse_is_active(data: object) -> None | Unset | bool:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | bool, data)

        is_active = _parse_is_active(d.pop("is_active", UNSET))

        identity_update = cls(
            role=role,
            claims=claims,
            is_active=is_active,
        )

        identity_update.additional_properties = d
        return identity_update

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
