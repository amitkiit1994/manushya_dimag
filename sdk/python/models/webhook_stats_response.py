from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="WebhookStatsResponse")


@_attrs_define
class WebhookStatsResponse:
    """
    Attributes:
        total_webhooks (int):
        active_webhooks (int):
        pending_deliveries (int):
        failed_deliveries (int):
        successful_deliveries (int):
    """

    total_webhooks: int
    active_webhooks: int
    pending_deliveries: int
    failed_deliveries: int
    successful_deliveries: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_webhooks = self.total_webhooks

        active_webhooks = self.active_webhooks

        pending_deliveries = self.pending_deliveries

        failed_deliveries = self.failed_deliveries

        successful_deliveries = self.successful_deliveries

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_webhooks": total_webhooks,
                "active_webhooks": active_webhooks,
                "pending_deliveries": pending_deliveries,
                "failed_deliveries": failed_deliveries,
                "successful_deliveries": successful_deliveries,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total_webhooks = d.pop("total_webhooks")

        active_webhooks = d.pop("active_webhooks")

        pending_deliveries = d.pop("pending_deliveries")

        failed_deliveries = d.pop("failed_deliveries")

        successful_deliveries = d.pop("successful_deliveries")

        webhook_stats_response = cls(
            total_webhooks=total_webhooks,
            active_webhooks=active_webhooks,
            pending_deliveries=pending_deliveries,
            failed_deliveries=failed_deliveries,
            successful_deliveries=successful_deliveries,
        )

        webhook_stats_response.additional_properties = d
        return webhook_stats_response

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
