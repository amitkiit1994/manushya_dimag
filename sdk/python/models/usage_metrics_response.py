from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.usage_metrics_response_last_24h_activity import (
        UsageMetricsResponseLast24HActivity,
    )


T = TypeVar("T", bound="UsageMetricsResponse")


@_attrs_define
class UsageMetricsResponse:
    """
    Attributes:
        total_identities (int):
        active_sessions (int):
        total_memories (int):
        total_api_keys (int):
        total_webhooks (int):
        total_invitations (int):
        rate_limit_violations (int):
        webhook_delivery_success_rate (float):
        memory_search_queries (int):
        last_24h_activity (UsageMetricsResponseLast24HActivity):
    """

    total_identities: int
    active_sessions: int
    total_memories: int
    total_api_keys: int
    total_webhooks: int
    total_invitations: int
    rate_limit_violations: int
    webhook_delivery_success_rate: float
    memory_search_queries: int
    last_24h_activity: "UsageMetricsResponseLast24HActivity"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_identities = self.total_identities

        active_sessions = self.active_sessions

        total_memories = self.total_memories

        total_api_keys = self.total_api_keys

        total_webhooks = self.total_webhooks

        total_invitations = self.total_invitations

        rate_limit_violations = self.rate_limit_violations

        webhook_delivery_success_rate = self.webhook_delivery_success_rate

        memory_search_queries = self.memory_search_queries

        last_24h_activity = self.last_24h_activity.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_identities": total_identities,
                "active_sessions": active_sessions,
                "total_memories": total_memories,
                "total_api_keys": total_api_keys,
                "total_webhooks": total_webhooks,
                "total_invitations": total_invitations,
                "rate_limit_violations": rate_limit_violations,
                "webhook_delivery_success_rate": webhook_delivery_success_rate,
                "memory_search_queries": memory_search_queries,
                "last_24h_activity": last_24h_activity,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.usage_metrics_response_last_24h_activity import (
            UsageMetricsResponseLast24HActivity,
        )

        d = dict(src_dict)
        total_identities = d.pop("total_identities")

        active_sessions = d.pop("active_sessions")

        total_memories = d.pop("total_memories")

        total_api_keys = d.pop("total_api_keys")

        total_webhooks = d.pop("total_webhooks")

        total_invitations = d.pop("total_invitations")

        rate_limit_violations = d.pop("rate_limit_violations")

        webhook_delivery_success_rate = d.pop("webhook_delivery_success_rate")

        memory_search_queries = d.pop("memory_search_queries")

        last_24h_activity = UsageMetricsResponseLast24HActivity.from_dict(
            d.pop("last_24h_activity")
        )

        usage_metrics_response = cls(
            total_identities=total_identities,
            active_sessions=active_sessions,
            total_memories=total_memories,
            total_api_keys=total_api_keys,
            total_webhooks=total_webhooks,
            total_invitations=total_invitations,
            rate_limit_violations=rate_limit_violations,
            webhook_delivery_success_rate=webhook_delivery_success_rate,
            memory_search_queries=memory_search_queries,
            last_24h_activity=last_24h_activity,
        )

        usage_metrics_response.additional_properties = d
        return usage_metrics_response

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
