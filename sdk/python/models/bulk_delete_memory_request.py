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

T = TypeVar("T", bound="BulkDeleteMemoryRequest")


@_attrs_define
class BulkDeleteMemoryRequest:
    """
    Attributes:
        memory_ids (list[UUID]): List of memory IDs to delete
        hard_delete (Union[Unset, bool]): Perform hard delete instead of soft delete Default: False.
        reason (Union[None, Unset, str]): Reason for bulk deletion
    """

    memory_ids: list[UUID]
    hard_delete: Unset | bool = False
    reason: None | Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        memory_ids = []
        for memory_ids_item_data in self.memory_ids:
            memory_ids_item = str(memory_ids_item_data)
            memory_ids.append(memory_ids_item)

        hard_delete = self.hard_delete

        reason: None | Unset | str
        if isinstance(self.reason, Unset):
            reason = UNSET
        else:
            reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "memory_ids": memory_ids,
            }
        )
        if hard_delete is not UNSET:
            field_dict["hard_delete"] = hard_delete
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        memory_ids = []
        _memory_ids = d.pop("memory_ids")
        for memory_ids_item_data in _memory_ids:
            memory_ids_item = UUID(memory_ids_item_data)

            memory_ids.append(memory_ids_item)

        hard_delete = d.pop("hard_delete", UNSET)

        def _parse_reason(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        reason = _parse_reason(d.pop("reason", UNSET))

        bulk_delete_memory_request = cls(
            memory_ids=memory_ids,
            hard_delete=hard_delete,
            reason=reason,
        )

        bulk_delete_memory_request.additional_properties = d
        return bulk_delete_memory_request

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
