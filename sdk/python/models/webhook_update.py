from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WebhookUpdate")


@_attrs_define
class WebhookUpdate:
    """
    Attributes:
        name (Union[None, Unset, str]): Webhook name
        url (Union[None, Unset, str]): Webhook URL
        events (Union[None, Unset, list[str]]): List of events to subscribe to
        is_active (Union[None, Unset, bool]): Whether webhook is active
    """

    name: None | Unset | str = UNSET
    url: None | Unset | str = UNSET
    events: None | Unset | list[str] = UNSET
    is_active: None | Unset | bool = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: None | Unset | str
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        url: None | Unset | str
        if isinstance(self.url, Unset):
            url = UNSET
        else:
            url = self.url

        events: None | Unset | list[str]
        if isinstance(self.events, Unset):
            events = UNSET
        elif isinstance(self.events, list):
            events = self.events

        else:
            events = self.events

        is_active: None | Unset | bool
        if isinstance(self.is_active, Unset):
            is_active = UNSET
        else:
            is_active = self.is_active

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if url is not UNSET:
            field_dict["url"] = url
        if events is not UNSET:
            field_dict["events"] = events
        if is_active is not UNSET:
            field_dict["is_active"] = is_active

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

        def _parse_url(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        url = _parse_url(d.pop("url", UNSET))

        def _parse_events(data: object) -> None | Unset | list[str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                events_type_0 = cast(list[str], data)

                return events_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | list[str], data)

        events = _parse_events(d.pop("events", UNSET))

        def _parse_is_active(data: object) -> None | Unset | bool:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | bool, data)

        is_active = _parse_is_active(d.pop("is_active", UNSET))

        webhook_update = cls(
            name=name,
            url=url,
            events=events,
            is_active=is_active,
        )

        webhook_update.additional_properties = d
        return webhook_update

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
