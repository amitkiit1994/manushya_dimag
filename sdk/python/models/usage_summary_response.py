from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.usage_summary_response_daily_breakdown_item import (
        UsageSummaryResponseDailyBreakdownItem,
    )
    from ..models.usage_summary_response_period import UsageSummaryResponsePeriod
    from ..models.usage_summary_response_totals import UsageSummaryResponseTotals


T = TypeVar("T", bound="UsageSummaryResponse")


@_attrs_define
class UsageSummaryResponse:
    """Usage summary response model.

    Attributes:
        tenant_id (str):
        period (UsageSummaryResponsePeriod):
        totals (UsageSummaryResponseTotals):
        daily_breakdown (list['UsageSummaryResponseDailyBreakdownItem']):
    """

    tenant_id: str
    period: "UsageSummaryResponsePeriod"
    totals: "UsageSummaryResponseTotals"
    daily_breakdown: list["UsageSummaryResponseDailyBreakdownItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tenant_id = self.tenant_id

        period = self.period.to_dict()

        totals = self.totals.to_dict()

        daily_breakdown = []
        for daily_breakdown_item_data in self.daily_breakdown:
            daily_breakdown_item = daily_breakdown_item_data.to_dict()
            daily_breakdown.append(daily_breakdown_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tenant_id": tenant_id,
                "period": period,
                "totals": totals,
                "daily_breakdown": daily_breakdown,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.usage_summary_response_daily_breakdown_item import (
            UsageSummaryResponseDailyBreakdownItem,
        )
        from ..models.usage_summary_response_period import UsageSummaryResponsePeriod
        from ..models.usage_summary_response_totals import UsageSummaryResponseTotals

        d = dict(src_dict)
        tenant_id = d.pop("tenant_id")

        period = UsageSummaryResponsePeriod.from_dict(d.pop("period"))

        totals = UsageSummaryResponseTotals.from_dict(d.pop("totals"))

        daily_breakdown = []
        _daily_breakdown = d.pop("daily_breakdown")
        for daily_breakdown_item_data in _daily_breakdown:
            daily_breakdown_item = UsageSummaryResponseDailyBreakdownItem.from_dict(
                daily_breakdown_item_data
            )

            daily_breakdown.append(daily_breakdown_item)

        usage_summary_response = cls(
            tenant_id=tenant_id,
            period=period,
            totals=totals,
            daily_breakdown=daily_breakdown,
        )

        usage_summary_response.additional_properties = d
        return usage_summary_response

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
