from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.bulk_delete_policy_response_failed_policies_item import (
        BulkDeletePolicyResponseFailedPoliciesItem,
    )


T = TypeVar("T", bound="BulkDeletePolicyResponse")


@_attrs_define
class BulkDeletePolicyResponse:
    """
    Attributes:
        deleted_count (int):
        failed_count (int):
        failed_policies (list['BulkDeletePolicyResponseFailedPoliciesItem']):
        message (str):
    """

    deleted_count: int
    failed_count: int
    failed_policies: list["BulkDeletePolicyResponseFailedPoliciesItem"]
    message: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        deleted_count = self.deleted_count

        failed_count = self.failed_count

        failed_policies = []
        for failed_policies_item_data in self.failed_policies:
            failed_policies_item = failed_policies_item_data.to_dict()
            failed_policies.append(failed_policies_item)

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "failed_policies": failed_policies,
                "message": message,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bulk_delete_policy_response_failed_policies_item import (
            BulkDeletePolicyResponseFailedPoliciesItem,
        )

        d = dict(src_dict)
        deleted_count = d.pop("deleted_count")

        failed_count = d.pop("failed_count")

        failed_policies = []
        _failed_policies = d.pop("failed_policies")
        for failed_policies_item_data in _failed_policies:
            failed_policies_item = BulkDeletePolicyResponseFailedPoliciesItem.from_dict(
                failed_policies_item_data
            )

            failed_policies.append(failed_policies_item)

        message = d.pop("message")

        bulk_delete_policy_response = cls(
            deleted_count=deleted_count,
            failed_count=failed_count,
            failed_policies=failed_policies,
            message=message,
        )

        bulk_delete_policy_response.additional_properties = d
        return bulk_delete_policy_response

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
