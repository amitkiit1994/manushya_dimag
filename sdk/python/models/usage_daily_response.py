import datetime
from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="UsageDailyResponse")


@_attrs_define
class UsageDailyResponse:
    """Daily usage response model.

    Attributes:
        id (str):
        tenant_id (str):
        date (datetime.date):
        event (str):
        units (int):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    tenant_id: str
    date: datetime.date
    event: str
    units: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        tenant_id = self.tenant_id

        date = self.date.isoformat()

        event = self.event

        units = self.units

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "tenant_id": tenant_id,
                "date": date,
                "event": event,
                "units": units,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        tenant_id = d.pop("tenant_id")

        date = isoparse(d.pop("date")).date()

        event = d.pop("event")

        units = d.pop("units")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        usage_daily_response = cls(
            id=id,
            tenant_id=tenant_id,
            date=date,
            event=event,
            units=units,
            created_at=created_at,
            updated_at=updated_at,
        )

        usage_daily_response.additional_properties = d
        return usage_daily_response

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
