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
    from ..models.event_response_metadata import EventResponseMetadata
    from ..models.event_response_payload import EventResponsePayload


T = TypeVar("T", bound="EventResponse")


@_attrs_define
class EventResponse:
    """
    Attributes:
        id (UUID):
        event_type (str):
        identity_id (Union[None, UUID]):
        actor_id (Union[None, UUID]):
        payload (EventResponsePayload):
        metadata (EventResponseMetadata):
        is_delivered (bool):
        delivery_attempts (int):
        delivered_at (Union[None, datetime.datetime]):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        tenant_id (Union[None, UUID, Unset]):
    """

    id: UUID
    event_type: str
    identity_id: None | UUID
    actor_id: None | UUID
    payload: "EventResponsePayload"
    metadata: "EventResponseMetadata"
    is_delivered: bool
    delivery_attempts: int
    delivered_at: None | datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tenant_id: None | UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        event_type = self.event_type

        identity_id: None | str
        if isinstance(self.identity_id, UUID):
            identity_id = str(self.identity_id)
        else:
            identity_id = self.identity_id

        actor_id: None | str
        if isinstance(self.actor_id, UUID):
            actor_id = str(self.actor_id)
        else:
            actor_id = self.actor_id

        payload = self.payload.to_dict()

        metadata = self.metadata.to_dict()

        is_delivered = self.is_delivered

        delivery_attempts = self.delivery_attempts

        delivered_at: None | str
        if isinstance(self.delivered_at, datetime.datetime):
            delivered_at = self.delivered_at.isoformat()
        else:
            delivered_at = self.delivered_at

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
                "event_type": event_type,
                "identity_id": identity_id,
                "actor_id": actor_id,
                "payload": payload,
                "metadata": metadata,
                "is_delivered": is_delivered,
                "delivery_attempts": delivery_attempts,
                "delivered_at": delivered_at,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if tenant_id is not UNSET:
            field_dict["tenant_id"] = tenant_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.event_response_metadata import EventResponseMetadata
        from ..models.event_response_payload import EventResponsePayload

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        event_type = d.pop("event_type")

        def _parse_identity_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                identity_id_type_0 = UUID(data)

                return identity_id_type_0
            except:  # noqa: E722
                pass
            return cast(None | UUID, data)

        identity_id = _parse_identity_id(d.pop("identity_id"))

        def _parse_actor_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                actor_id_type_0 = UUID(data)

                return actor_id_type_0
            except:  # noqa: E722
                pass
            return cast(None | UUID, data)

        actor_id = _parse_actor_id(d.pop("actor_id"))

        payload = EventResponsePayload.from_dict(d.pop("payload"))

        metadata = EventResponseMetadata.from_dict(d.pop("metadata"))

        is_delivered = d.pop("is_delivered")

        delivery_attempts = d.pop("delivery_attempts")

        def _parse_delivered_at(data: object) -> None | datetime.datetime:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                delivered_at_type_0 = isoparse(data)

                return delivered_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | datetime.datetime, data)

        delivered_at = _parse_delivered_at(d.pop("delivered_at"))

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

        event_response = cls(
            id=id,
            event_type=event_type,
            identity_id=identity_id,
            actor_id=actor_id,
            payload=payload,
            metadata=metadata,
            is_delivered=is_delivered,
            delivery_attempts=delivery_attempts,
            delivered_at=delivered_at,
            created_at=created_at,
            updated_at=updated_at,
            tenant_id=tenant_id,
        )

        event_response.additional_properties = d
        return event_response

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
