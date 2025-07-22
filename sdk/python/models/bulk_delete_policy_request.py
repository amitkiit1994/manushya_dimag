from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    cast,
)
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BulkDeletePolicyRequest")


@_attrs_define
class BulkDeletePolicyRequest:
    """
    Attributes:
        policy_ids (list[UUID]): List of policy IDs to delete
        reason (Union[None, Unset, str]): Reason for bulk deletion
    """

    policy_ids: list[UUID]
    reason: None | Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        policy_ids = []
        for policy_ids_item_data in self.policy_ids:
            policy_ids_item = str(policy_ids_item_data)
            policy_ids.append(policy_ids_item)

        reason: None | Unset | str
        if isinstance(self.reason, Unset):
            reason = UNSET
        else:
            reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "policy_ids": policy_ids,
            }
        )
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        policy_ids = []
        _policy_ids = d.pop("policy_ids")
        for policy_ids_item_data in _policy_ids:
            policy_ids_item = UUID(policy_ids_item_data)

            policy_ids.append(policy_ids_item)

        def _parse_reason(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        reason = _parse_reason(d.pop("reason", UNSET))

        bulk_delete_policy_request = cls(
            policy_ids=policy_ids,
            reason=reason,
        )

        bulk_delete_policy_request.additional_properties = d
        return bulk_delete_policy_request

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
