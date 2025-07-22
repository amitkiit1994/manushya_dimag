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
    from ..models.memory_response_meta_data import MemoryResponseMetaData


T = TypeVar("T", bound="MemoryResponse")


@_attrs_define
class MemoryResponse:
    """
    Attributes:
        id (UUID):
        identity_id (UUID):
        text (str):
        type_ (str):
        meta_data (MemoryResponseMetaData):
        score (Union[None, float]):
        version (int):
        ttl_days (Union[None, int]):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        tenant_id (Union[None, UUID, Unset]):
    """

    id: UUID
    identity_id: UUID
    text: str
    type_: str
    meta_data: "MemoryResponseMetaData"
    score: None | float
    version: int
    ttl_days: None | int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tenant_id: None | UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        identity_id = str(self.identity_id)

        text = self.text

        type_ = self.type_

        meta_data = self.meta_data.to_dict()

        score: None | float
        score = self.score

        version = self.version

        ttl_days: None | int
        ttl_days = self.ttl_days

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
                "identity_id": identity_id,
                "text": text,
                "type": type_,
                "meta_data": meta_data,
                "score": score,
                "version": version,
                "ttl_days": ttl_days,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if tenant_id is not UNSET:
            field_dict["tenant_id"] = tenant_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.memory_response_meta_data import MemoryResponseMetaData

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        identity_id = UUID(d.pop("identity_id"))

        text = d.pop("text")

        type_ = d.pop("type")

        meta_data = MemoryResponseMetaData.from_dict(d.pop("meta_data"))

        def _parse_score(data: object) -> None | float:
            if data is None:
                return data
            return cast(None | float, data)

        score = _parse_score(d.pop("score"))

        version = d.pop("version")

        def _parse_ttl_days(data: object) -> None | int:
            if data is None:
                return data
            return cast(None | int, data)

        ttl_days = _parse_ttl_days(d.pop("ttl_days"))

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

        memory_response = cls(
            id=id,
            identity_id=identity_id,
            text=text,
            type_=type_,
            meta_data=meta_data,
            score=score,
            version=version,
            ttl_days=ttl_days,
            created_at=created_at,
            updated_at=updated_at,
            tenant_id=tenant_id,
        )

        memory_response.additional_properties = d
        return memory_response

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
