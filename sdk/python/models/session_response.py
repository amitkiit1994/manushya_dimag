import datetime
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    cast,
)
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.session_response_device_info import SessionResponseDeviceInfo


T = TypeVar("T", bound="SessionResponse")


@_attrs_define
class SessionResponse:
    """
    Attributes:
        id (UUID):
        device_info (SessionResponseDeviceInfo):
        ip_address (Union[None, str]):
        user_agent (Union[None, str]):
        is_active (bool):
        expires_at (datetime.datetime):
        last_used_at (datetime.datetime):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        tenant_id (Union[None, UUID, Unset]):
    """

    id: UUID
    device_info: "SessionResponseDeviceInfo"
    ip_address: None | str
    user_agent: None | str
    is_active: bool
    expires_at: datetime.datetime
    last_used_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tenant_id: None | UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        device_info = self.device_info.to_dict()

        ip_address: None | str
        ip_address = self.ip_address

        user_agent: None | str
        user_agent = self.user_agent

        is_active = self.is_active

        expires_at = self.expires_at.isoformat()

        last_used_at = self.last_used_at.isoformat()

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
                "device_info": device_info,
                "ip_address": ip_address,
                "user_agent": user_agent,
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
        from ..models.session_response_device_info import SessionResponseDeviceInfo

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        device_info = SessionResponseDeviceInfo.from_dict(d.pop("device_info"))

        def _parse_ip_address(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        ip_address = _parse_ip_address(d.pop("ip_address"))

        def _parse_user_agent(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        user_agent = _parse_user_agent(d.pop("user_agent"))

        is_active = d.pop("is_active")

        expires_at = isoparse(d.pop("expires_at"))

        last_used_at = isoparse(d.pop("last_used_at"))

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

        session_response = cls(
            id=id,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=is_active,
            expires_at=expires_at,
            last_used_at=last_used_at,
            created_at=created_at,
            updated_at=updated_at,
            tenant_id=tenant_id,
        )

        session_response.additional_properties = d
        return session_response

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
