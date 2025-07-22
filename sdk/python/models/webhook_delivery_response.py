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

T = TypeVar("T", bound="WebhookDeliveryResponse")


@_attrs_define
class WebhookDeliveryResponse:
    """
    Attributes:
        id (UUID):
        webhook_id (UUID):
        event_type (str):
        status (str):
        delivery_attempts (int):
        created_at (datetime.datetime):
        response_code (Union[None, Unset, int]):
        next_retry_at (Union[None, Unset, datetime.datetime]):
        delivered_at (Union[None, Unset, datetime.datetime]):
    """

    id: UUID
    webhook_id: UUID
    event_type: str
    status: str
    delivery_attempts: int
    created_at: datetime.datetime
    response_code: None | Unset | int = UNSET
    next_retry_at: None | Unset | datetime.datetime = UNSET
    delivered_at: None | Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        webhook_id = str(self.webhook_id)

        event_type = self.event_type

        status = self.status

        delivery_attempts = self.delivery_attempts

        created_at = self.created_at.isoformat()

        response_code: None | Unset | int
        if isinstance(self.response_code, Unset):
            response_code = UNSET
        else:
            response_code = self.response_code

        next_retry_at: None | Unset | str
        if isinstance(self.next_retry_at, Unset):
            next_retry_at = UNSET
        elif isinstance(self.next_retry_at, datetime.datetime):
            next_retry_at = self.next_retry_at.isoformat()
        else:
            next_retry_at = self.next_retry_at

        delivered_at: None | Unset | str
        if isinstance(self.delivered_at, Unset):
            delivered_at = UNSET
        elif isinstance(self.delivered_at, datetime.datetime):
            delivered_at = self.delivered_at.isoformat()
        else:
            delivered_at = self.delivered_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "webhook_id": webhook_id,
                "event_type": event_type,
                "status": status,
                "delivery_attempts": delivery_attempts,
                "created_at": created_at,
            }
        )
        if response_code is not UNSET:
            field_dict["response_code"] = response_code
        if next_retry_at is not UNSET:
            field_dict["next_retry_at"] = next_retry_at
        if delivered_at is not UNSET:
            field_dict["delivered_at"] = delivered_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        webhook_id = UUID(d.pop("webhook_id"))

        event_type = d.pop("event_type")

        status = d.pop("status")

        delivery_attempts = d.pop("delivery_attempts")

        created_at = isoparse(d.pop("created_at"))

        def _parse_response_code(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        response_code = _parse_response_code(d.pop("response_code", UNSET))

        def _parse_next_retry_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                next_retry_at_type_0 = isoparse(data)

                return next_retry_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        next_retry_at = _parse_next_retry_at(d.pop("next_retry_at", UNSET))

        def _parse_delivered_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                delivered_at_type_0 = isoparse(data)

                return delivered_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        delivered_at = _parse_delivered_at(d.pop("delivered_at", UNSET))

        webhook_delivery_response = cls(
            id=id,
            webhook_id=webhook_id,
            event_type=event_type,
            status=status,
            delivery_attempts=delivery_attempts,
            created_at=created_at,
            response_code=response_code,
            next_retry_at=next_retry_at,
            delivered_at=delivered_at,
        )

        webhook_delivery_response.additional_properties = d
        return webhook_delivery_response

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
