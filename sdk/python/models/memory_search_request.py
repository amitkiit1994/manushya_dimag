from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MemorySearchRequest")


@_attrs_define
class MemorySearchRequest:
    """
    Attributes:
        query (str): Search query
        type_ (Union[None, Unset, str]): Filter by memory type
        limit (Union[Unset, int]): Maximum number of results Default: 10.
        similarity_threshold (Union[Unset, float]): Minimum similarity score Default: 0.7.
    """

    query: str
    type_: None | Unset | str = UNSET
    limit: Unset | int = 10
    similarity_threshold: Unset | float = 0.7
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        query = self.query

        type_: None | Unset | str
        if isinstance(self.type_, Unset):
            type_ = UNSET
        else:
            type_ = self.type_

        limit = self.limit

        similarity_threshold = self.similarity_threshold

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "query": query,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_
        if limit is not UNSET:
            field_dict["limit"] = limit
        if similarity_threshold is not UNSET:
            field_dict["similarity_threshold"] = similarity_threshold

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        query = d.pop("query")

        def _parse_type_(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        type_ = _parse_type_(d.pop("type", UNSET))

        limit = d.pop("limit", UNSET)

        similarity_threshold = d.pop("similarity_threshold", UNSET)

        memory_search_request = cls(
            query=query,
            type_=type_,
            limit=limit,
            similarity_threshold=similarity_threshold,
        )

        memory_search_request.additional_properties = d
        return memory_search_request

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
