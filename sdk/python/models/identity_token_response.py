from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.identity_response import IdentityResponse


T = TypeVar("T", bound="IdentityTokenResponse")


@_attrs_define
class IdentityTokenResponse:
    """
    Attributes:
        access_token (str):
        identity (IdentityResponse):
        refresh_token (Union[None, Unset, str]):
        token_type (Union[Unset, str]):  Default: 'bearer'.
    """

    access_token: str
    identity: "IdentityResponse"
    refresh_token: None | Unset | str = UNSET
    token_type: Unset | str = "bearer"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_token = self.access_token

        identity = self.identity.to_dict()

        refresh_token: None | Unset | str
        if isinstance(self.refresh_token, Unset):
            refresh_token = UNSET
        else:
            refresh_token = self.refresh_token

        token_type = self.token_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "access_token": access_token,
                "identity": identity,
            }
        )
        if refresh_token is not UNSET:
            field_dict["refresh_token"] = refresh_token
        if token_type is not UNSET:
            field_dict["token_type"] = token_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.identity_response import IdentityResponse

        d = dict(src_dict)
        access_token = d.pop("access_token")

        identity = IdentityResponse.from_dict(d.pop("identity"))

        def _parse_refresh_token(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        refresh_token = _parse_refresh_token(d.pop("refresh_token", UNSET))

        token_type = d.pop("token_type", UNSET)

        identity_token_response = cls(
            access_token=access_token,
            identity=identity,
            refresh_token=refresh_token,
            token_type=token_type,
        )

        identity_token_response.additional_properties = d
        return identity_token_response

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
