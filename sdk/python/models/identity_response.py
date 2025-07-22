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
    from ..models.identity_response_claims import IdentityResponseClaims


T = TypeVar("T", bound="IdentityResponse")


@_attrs_define
class IdentityResponse:
    """
    Attributes:
        id (UUID):
        external_id (str):
        role (str):
        claims (IdentityResponseClaims):
        is_active (bool):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        tenant_id (Union[None, UUID, Unset]):
    """

    id: UUID
    external_id: str
    role: str
    claims: "IdentityResponseClaims"
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tenant_id: None | UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        external_id = self.external_id

        role = self.role

        claims = self.claims.to_dict()

        is_active = self.is_active

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
                "external_id": external_id,
                "role": role,
                "claims": claims,
                "is_active": is_active,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if tenant_id is not UNSET:
            field_dict["tenant_id"] = tenant_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.identity_response_claims import IdentityResponseClaims

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        external_id = d.pop("external_id")

        role = d.pop("role")

        claims = IdentityResponseClaims.from_dict(d.pop("claims"))

        is_active = d.pop("is_active")

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

        identity_response = cls(
            id=id,
            external_id=external_id,
            role=role,
            claims=claims,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at,
            tenant_id=tenant_id,
        )

        identity_response.additional_properties = d
        return identity_response

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
