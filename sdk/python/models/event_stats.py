from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.event_stats_event_types import EventStatsEventTypes


T = TypeVar("T", bound="EventStats")


@_attrs_define
class EventStats:
    """
    Attributes:
        total_events (int):
        delivered_events (int):
        undelivered_events (int):
        event_types (EventStatsEventTypes):
    """

    total_events: int
    delivered_events: int
    undelivered_events: int
    event_types: "EventStatsEventTypes"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_events = self.total_events

        delivered_events = self.delivered_events

        undelivered_events = self.undelivered_events

        event_types = self.event_types.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_events": total_events,
                "delivered_events": delivered_events,
                "undelivered_events": undelivered_events,
                "event_types": event_types,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.event_stats_event_types import EventStatsEventTypes

        d = dict(src_dict)
        total_events = d.pop("total_events")

        delivered_events = d.pop("delivered_events")

        undelivered_events = d.pop("undelivered_events")

        event_types = EventStatsEventTypes.from_dict(d.pop("event_types"))

        event_stats = cls(
            total_events=total_events,
            delivered_events=delivered_events,
            undelivered_events=undelivered_events,
            event_types=event_types,
        )

        event_stats.additional_properties = d
        return event_stats

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
