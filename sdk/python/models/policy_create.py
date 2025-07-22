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
    from ..models.policy_create_rule import PolicyCreateRule


T = TypeVar("T", bound="PolicyCreate")


@_attrs_define
class PolicyCreate:
    """
    Attributes:
        role (str): Role this policy applies to
        rule (PolicyCreateRule): JSON Logic rule
        description (Union[None, Unset, str]): Policy description
        priority (Union[Unset, int]): Policy priority (higher = more important) Default: 0.
        is_active (Union[Unset, bool]): Whether the policy is active Default: True.
    """

    role: str
    rule: "PolicyCreateRule"
    description: None | Unset | str = UNSET
    priority: Unset | int = 0
    is_active: Unset | bool = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        role = self.role

        rule = self.rule.to_dict()

        description: None | Unset | str
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        priority = self.priority

        is_active = self.is_active

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "role": role,
                "rule": rule,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if priority is not UNSET:
            field_dict["priority"] = priority
        if is_active is not UNSET:
            field_dict["is_active"] = is_active

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.policy_create_rule import PolicyCreateRule

        d = dict(src_dict)
        role = d.pop("role")

        rule = PolicyCreateRule.from_dict(d.pop("rule"))

        def _parse_description(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        description = _parse_description(d.pop("description", UNSET))

        priority = d.pop("priority", UNSET)

        is_active = d.pop("is_active", UNSET)

        policy_create = cls(
            role=role,
            rule=rule,
            description=description,
            priority=priority,
            is_active=is_active,
        )

        policy_create.additional_properties = d
        return policy_create

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
