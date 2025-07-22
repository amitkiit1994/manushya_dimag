import datetime
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.usage_event_response_event_metadata import (
        UsageEventResponseEventMetadata,
    )


T = TypeVar("T", bound="UsageEventResponse")


@_attrs_define
class UsageEventResponse:
    """Usage event response model.

    Attributes:
        id (str):
        tenant_id (str):
        event (str):
        units (int):
        event_metadata (UsageEventResponseEventMetadata):
        created_at (datetime.datetime):
        api_key_id (Union[None, Unset, str]):
        identity_id (Union[None, Unset, str]):
    """

    id: str
    tenant_id: str
    event: str
    units: int
    event_metadata: "UsageEventResponseEventMetadata"
    created_at: datetime.datetime
    api_key_id: None | Unset | str = UNSET
    identity_id: None | Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        tenant_id = self.tenant_id

        event = self.event

        units = self.units

        event_metadata = self.event_metadata.to_dict()

        created_at = self.created_at.isoformat()

        api_key_id: None | Unset | str
        if isinstance(self.api_key_id, Unset):
            api_key_id = UNSET
        else:
            api_key_id = self.api_key_id

        identity_id: None | Unset | str
        if isinstance(self.identity_id, Unset):
            identity_id = UNSET
        else:
            identity_id = self.identity_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "tenant_id": tenant_id,
                "event": event,
                "units": units,
                "event_metadata": event_metadata,
                "created_at": created_at,
            }
        )
        if api_key_id is not UNSET:
            field_dict["api_key_id"] = api_key_id
        if identity_id is not UNSET:
            field_dict["identity_id"] = identity_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.usage_event_response_event_metadata import (
            UsageEventResponseEventMetadata,
        )

        d = dict(src_dict)
        id = d.pop("id")

        tenant_id = d.pop("tenant_id")

        event = d.pop("event")

        units = d.pop("units")

        event_metadata = UsageEventResponseEventMetadata.from_dict(
            d.pop("event_metadata")
        )

        created_at = isoparse(d.pop("created_at"))

        def _parse_api_key_id(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        api_key_id = _parse_api_key_id(d.pop("api_key_id", UNSET))

        def _parse_identity_id(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        identity_id = _parse_identity_id(d.pop("identity_id", UNSET))

        usage_event_response = cls(
            id=id,
            tenant_id=tenant_id,
            event=event,
            units=units,
            event_metadata=event_metadata,
            created_at=created_at,
            api_key_id=api_key_id,
            identity_id=identity_id,
        )

        usage_event_response.additional_properties = d
        return usage_event_response

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
