from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.memory_create_metadata import MemoryCreateMetadata


T = TypeVar("T", bound="MemoryCreate")


@_attrs_define
class MemoryCreate:
    """
    Attributes:
        text (str): Memory text content
        type_ (str): Type of memory
        metadata (Union[Unset, MemoryCreateMetadata]): Additional metadata
        ttl_days (Union[None, Unset, int]): Time to live in days
    """

    text: str
    type_: str
    metadata: Union[Unset, "MemoryCreateMetadata"] = UNSET
    ttl_days: None | Unset | int = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        text = self.text

        type_ = self.type_

        metadata: Unset | dict[str, Any] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        ttl_days: None | Unset | int
        if isinstance(self.ttl_days, Unset):
            ttl_days = UNSET
        else:
            ttl_days = self.ttl_days

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "text": text,
                "type": type_,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if ttl_days is not UNSET:
            field_dict["ttl_days"] = ttl_days

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.memory_create_metadata import MemoryCreateMetadata

        d = dict(src_dict)
        text = d.pop("text")

        type_ = d.pop("type")

        _metadata = d.pop("metadata", UNSET)
        metadata: Unset | MemoryCreateMetadata
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = MemoryCreateMetadata.from_dict(_metadata)

        def _parse_ttl_days(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        ttl_days = _parse_ttl_days(d.pop("ttl_days", UNSET))

        memory_create = cls(
            text=text,
            type_=type_,
            metadata=metadata,
            ttl_days=ttl_days,
        )

        memory_create.additional_properties = d
        return memory_create

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
