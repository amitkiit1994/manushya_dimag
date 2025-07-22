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
    from ..models.memory_update_metadata_type_0 import MemoryUpdateMetadataType0


T = TypeVar("T", bound="MemoryUpdate")


@_attrs_define
class MemoryUpdate:
    """
    Attributes:
        text (Union[None, Unset, str]): Memory text content
        type_ (Union[None, Unset, str]): Type of memory
        metadata (Union['MemoryUpdateMetadataType0', None, Unset]): Additional metadata
        ttl_days (Union[None, Unset, int]): Time to live in days
    """

    text: None | Unset | str = UNSET
    type_: None | Unset | str = UNSET
    metadata: Union["MemoryUpdateMetadataType0", None, Unset] = UNSET
    ttl_days: None | Unset | int = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.memory_update_metadata_type_0 import MemoryUpdateMetadataType0

        text: None | Unset | str
        if isinstance(self.text, Unset):
            text = UNSET
        else:
            text = self.text

        type_: None | Unset | str
        if isinstance(self.type_, Unset):
            type_ = UNSET
        else:
            type_ = self.type_

        metadata: None | Unset | dict[str, Any]
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, MemoryUpdateMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        ttl_days: None | Unset | int
        if isinstance(self.ttl_days, Unset):
            ttl_days = UNSET
        else:
            ttl_days = self.ttl_days

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if text is not UNSET:
            field_dict["text"] = text
        if type_ is not UNSET:
            field_dict["type"] = type_
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if ttl_days is not UNSET:
            field_dict["ttl_days"] = ttl_days

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.memory_update_metadata_type_0 import MemoryUpdateMetadataType0

        d = dict(src_dict)

        def _parse_text(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        text = _parse_text(d.pop("text", UNSET))

        def _parse_type_(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        type_ = _parse_type_(d.pop("type", UNSET))

        def _parse_metadata(
            data: object,
        ) -> Union["MemoryUpdateMetadataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = MemoryUpdateMetadataType0.from_dict(data)

                return metadata_type_0
            except:  # noqa: E722
                pass
            return cast(Union["MemoryUpdateMetadataType0", None, Unset], data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_ttl_days(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        ttl_days = _parse_ttl_days(d.pop("ttl_days", UNSET))

        memory_update = cls(
            text=text,
            type_=type_,
            metadata=metadata,
            ttl_days=ttl_days,
        )

        memory_update.additional_properties = d
        return memory_update

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
