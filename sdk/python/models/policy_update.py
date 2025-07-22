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
    from ..models.policy_update_rule_type_0 import PolicyUpdateRuleType0


T = TypeVar("T", bound="PolicyUpdate")


@_attrs_define
class PolicyUpdate:
    """
    Attributes:
        rule (Union['PolicyUpdateRuleType0', None, Unset]): JSON Logic rule
        description (Union[None, Unset, str]): Policy description
        priority (Union[None, Unset, int]): Policy priority
        is_active (Union[None, Unset, bool]): Whether the policy is active
    """

    rule: Union["PolicyUpdateRuleType0", None, Unset] = UNSET
    description: None | Unset | str = UNSET
    priority: None | Unset | int = UNSET
    is_active: None | Unset | bool = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.policy_update_rule_type_0 import PolicyUpdateRuleType0

        rule: None | Unset | dict[str, Any]
        if isinstance(self.rule, Unset):
            rule = UNSET
        elif isinstance(self.rule, PolicyUpdateRuleType0):
            rule = self.rule.to_dict()
        else:
            rule = self.rule

        description: None | Unset | str
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        priority: None | Unset | int
        if isinstance(self.priority, Unset):
            priority = UNSET
        else:
            priority = self.priority

        is_active: None | Unset | bool
        if isinstance(self.is_active, Unset):
            is_active = UNSET
        else:
            is_active = self.is_active

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if rule is not UNSET:
            field_dict["rule"] = rule
        if description is not UNSET:
            field_dict["description"] = description
        if priority is not UNSET:
            field_dict["priority"] = priority
        if is_active is not UNSET:
            field_dict["is_active"] = is_active

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.policy_update_rule_type_0 import PolicyUpdateRuleType0

        d = dict(src_dict)

        def _parse_rule(data: object) -> Union["PolicyUpdateRuleType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                rule_type_0 = PolicyUpdateRuleType0.from_dict(data)

                return rule_type_0
            except:  # noqa: E722
                pass
            return cast(Union["PolicyUpdateRuleType0", None, Unset], data)

        rule = _parse_rule(d.pop("rule", UNSET))

        def _parse_description(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_priority(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        priority = _parse_priority(d.pop("priority", UNSET))

        def _parse_is_active(data: object) -> None | Unset | bool:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | bool, data)

        is_active = _parse_is_active(d.pop("is_active", UNSET))

        policy_update = cls(
            rule=rule,
            description=description,
            priority=priority,
            is_active=is_active,
        )

        policy_update.additional_properties = d
        return policy_update

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
