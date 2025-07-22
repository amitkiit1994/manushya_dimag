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
    from ..models.invitation_response_claims import InvitationResponseClaims


T = TypeVar("T", bound="InvitationResponse")


@_attrs_define
class InvitationResponse:
    """
    Attributes:
        id (UUID):
        email (str):
        role (str):
        claims (InvitationResponseClaims):
        is_accepted (bool):
        accepted_at (Union[None, datetime.datetime]):
        expires_at (datetime.datetime):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        tenant_id (UUID):
        invited_by (Union[None, UUID, Unset]):
    """

    id: UUID
    email: str
    role: str
    claims: "InvitationResponseClaims"
    is_accepted: bool
    accepted_at: None | datetime.datetime
    expires_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tenant_id: UUID
    invited_by: None | UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        email = self.email

        role = self.role

        claims = self.claims.to_dict()

        is_accepted = self.is_accepted

        accepted_at: None | str
        if isinstance(self.accepted_at, datetime.datetime):
            accepted_at = self.accepted_at.isoformat()
        else:
            accepted_at = self.accepted_at

        expires_at = self.expires_at.isoformat()

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        tenant_id = str(self.tenant_id)

        invited_by: None | Unset | str
        if isinstance(self.invited_by, Unset):
            invited_by = UNSET
        elif isinstance(self.invited_by, UUID):
            invited_by = str(self.invited_by)
        else:
            invited_by = self.invited_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "email": email,
                "role": role,
                "claims": claims,
                "is_accepted": is_accepted,
                "accepted_at": accepted_at,
                "expires_at": expires_at,
                "created_at": created_at,
                "updated_at": updated_at,
                "tenant_id": tenant_id,
            }
        )
        if invited_by is not UNSET:
            field_dict["invited_by"] = invited_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.invitation_response_claims import InvitationResponseClaims

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        email = d.pop("email")

        role = d.pop("role")

        claims = InvitationResponseClaims.from_dict(d.pop("claims"))

        is_accepted = d.pop("is_accepted")

        def _parse_accepted_at(data: object) -> None | datetime.datetime:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                accepted_at_type_0 = isoparse(data)

                return accepted_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | datetime.datetime, data)

        accepted_at = _parse_accepted_at(d.pop("accepted_at"))

        expires_at = isoparse(d.pop("expires_at"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        tenant_id = UUID(d.pop("tenant_id"))

        def _parse_invited_by(data: object) -> None | UUID | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                invited_by_type_0 = UUID(data)

                return invited_by_type_0
            except:  # noqa: E722
                pass
            return cast(None | UUID | Unset, data)

        invited_by = _parse_invited_by(d.pop("invited_by", UNSET))

        invitation_response = cls(
            id=id,
            email=email,
            role=role,
            claims=claims,
            is_accepted=is_accepted,
            accepted_at=accepted_at,
            expires_at=expires_at,
            created_at=created_at,
            updated_at=updated_at,
            tenant_id=tenant_id,
            invited_by=invited_by,
        )

        invitation_response.additional_properties = d
        return invitation_response

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
