from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ApiKeyUpdate")


@_attrs_define
class ApiKeyUpdate:
    """
    Attributes:
        name (Union[None, Unset, str]): Name for the API key
        scopes (Union[None, Unset, list[str]]): List of scopes for the API key
        is_active (Union[None, Unset, bool]): Whether the API key is active
        expires_in_days (Union[None, Unset, int]): Expiration in days (optional)
    """

    name: None | Unset | str = UNSET
    scopes: None | Unset | list[str] = UNSET
    is_active: None | Unset | bool = UNSET
    expires_in_days: None | Unset | int = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: None | Unset | str
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        scopes: None | Unset | list[str]
        if isinstance(self.scopes, Unset):
            scopes = UNSET
        elif isinstance(self.scopes, list):
            scopes = self.scopes

        else:
            scopes = self.scopes

        is_active: None | Unset | bool
        if isinstance(self.is_active, Unset):
            is_active = UNSET
        else:
            is_active = self.is_active

        expires_in_days: None | Unset | int
        if isinstance(self.expires_in_days, Unset):
            expires_in_days = UNSET
        else:
            expires_in_days = self.expires_in_days

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if scopes is not UNSET:
            field_dict["scopes"] = scopes
        if is_active is not UNSET:
            field_dict["is_active"] = is_active
        if expires_in_days is not UNSET:
            field_dict["expires_in_days"] = expires_in_days

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_scopes(data: object) -> None | Unset | list[str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                scopes_type_0 = cast(list[str], data)

                return scopes_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | list[str], data)

        scopes = _parse_scopes(d.pop("scopes", UNSET))

        def _parse_is_active(data: object) -> None | Unset | bool:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | bool, data)

        is_active = _parse_is_active(d.pop("is_active", UNSET))

        def _parse_expires_in_days(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        expires_in_days = _parse_expires_in_days(d.pop("expires_in_days", UNSET))

        api_key_update = cls(
            name=name,
            scopes=scopes,
            is_active=is_active,
            expires_in_days=expires_in_days,
        )

        api_key_update.additional_properties = d
        return api_key_update

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
