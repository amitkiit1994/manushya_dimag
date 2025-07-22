import datetime
from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    cast,
)
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ApiKeyResponse")


@_attrs_define
class ApiKeyResponse:
    """
    Attributes:
        id (UUID):
        name (str):
        scopes (list[str]):
        is_active (bool):
        expires_at (Union[None, datetime.datetime]):
        last_used_at (Union[None, datetime.datetime]):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        tenant_id (Union[None, UUID, Unset]):
    """

    id: UUID
    name: str
    scopes: list[str]
    is_active: bool
    expires_at: None | datetime.datetime
    last_used_at: None | datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tenant_id: None | UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        scopes = self.scopes

        is_active = self.is_active

        expires_at: None | str
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        last_used_at: None | str
        if isinstance(self.last_used_at, datetime.datetime):
            last_used_at = self.last_used_at.isoformat()
        else:
            last_used_at = self.last_used_at

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        tenant_id: None | Unset | str
        if isinstance(self.tenant_id, Unset):
            tenant_id = UNSET
        elif isinstance(self.tenant_id, UUID):
            tenant_id = str(self.tenant_id)
        else:
            tenant_id = self.tenant_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "scopes": scopes,
                "is_active": is_active,
                "expires_at": expires_at,
                "last_used_at": last_used_at,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if tenant_id is not UNSET:
            field_dict["tenant_id"] = tenant_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        scopes = cast(list[str], d.pop("scopes"))

        is_active = d.pop("is_active")

        def _parse_expires_at(data: object) -> None | datetime.datetime:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = isoparse(data)

                return expires_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | datetime.datetime, data)

        expires_at = _parse_expires_at(d.pop("expires_at"))

        def _parse_last_used_at(data: object) -> None | datetime.datetime:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_used_at_type_0 = isoparse(data)

                return last_used_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | datetime.datetime, data)

        last_used_at = _parse_last_used_at(d.pop("last_used_at"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        def _parse_tenant_id(data: object) -> None | UUID | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                tenant_id_type_0 = UUID(data)

                return tenant_id_type_0
            except:  # noqa: E722
                pass
            return cast(None | UUID | Unset, data)

        tenant_id = _parse_tenant_id(d.pop("tenant_id", UNSET))

        api_key_response = cls(
            id=id,
            name=name,
            scopes=scopes,
            is_active=is_active,
            expires_at=expires_at,
            last_used_at=last_used_at,
            created_at=created_at,
            updated_at=updated_at,
            tenant_id=tenant_id,
        )

        api_key_response.additional_properties = d
        return api_key_response

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
