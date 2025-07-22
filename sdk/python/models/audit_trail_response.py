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

if TYPE_CHECKING:
    from ..models.audit_trail_response_after_state import AuditTrailResponseAfterState
    from ..models.audit_trail_response_before_state import AuditTrailResponseBeforeState


T = TypeVar("T", bound="AuditTrailResponse")


@_attrs_define
class AuditTrailResponse:
    """
    Attributes:
        event_type (str):
        actor_id (str):
        resource_type (str):
        resource_id (str):
        tenant_id (str):
        timestamp (datetime.datetime):
        before_state (AuditTrailResponseBeforeState):
        after_state (AuditTrailResponseAfterState):
        ip_address (Union[None, str]):
        user_agent (Union[None, str]):
    """

    event_type: str
    actor_id: str
    resource_type: str
    resource_id: str
    tenant_id: str
    timestamp: datetime.datetime
    before_state: "AuditTrailResponseBeforeState"
    after_state: "AuditTrailResponseAfterState"
    ip_address: None | str
    user_agent: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        event_type = self.event_type

        actor_id = self.actor_id

        resource_type = self.resource_type

        resource_id = self.resource_id

        tenant_id = self.tenant_id

        timestamp = self.timestamp.isoformat()

        before_state = self.before_state.to_dict()

        after_state = self.after_state.to_dict()

        ip_address: None | str
        ip_address = self.ip_address

        user_agent: None | str
        user_agent = self.user_agent

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "event_type": event_type,
                "actor_id": actor_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "tenant_id": tenant_id,
                "timestamp": timestamp,
                "before_state": before_state,
                "after_state": after_state,
                "ip_address": ip_address,
                "user_agent": user_agent,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.audit_trail_response_after_state import (
            AuditTrailResponseAfterState,
        )
        from ..models.audit_trail_response_before_state import (
            AuditTrailResponseBeforeState,
        )

        d = dict(src_dict)
        event_type = d.pop("event_type")

        actor_id = d.pop("actor_id")

        resource_type = d.pop("resource_type")

        resource_id = d.pop("resource_id")

        tenant_id = d.pop("tenant_id")

        timestamp = isoparse(d.pop("timestamp"))

        before_state = AuditTrailResponseBeforeState.from_dict(d.pop("before_state"))

        after_state = AuditTrailResponseAfterState.from_dict(d.pop("after_state"))

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

        audit_trail_response = cls(
            event_type=event_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
            timestamp=timestamp,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        audit_trail_response.additional_properties = d
        return audit_trail_response

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
