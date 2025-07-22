from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PerformanceMetricsResponse")


@_attrs_define
class PerformanceMetricsResponse:
    """
    Attributes:
        avg_response_time_ms (float):
        p95_response_time_ms (float):
        p99_response_time_ms (float):
        requests_per_second (float):
        error_rate_percent (float):
        database_connections (int):
        redis_memory_usage_mb (float):
        background_task_queue_size (int):
    """

    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate_percent: float
    database_connections: int
    redis_memory_usage_mb: float
    background_task_queue_size: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        avg_response_time_ms = self.avg_response_time_ms

        p95_response_time_ms = self.p95_response_time_ms

        p99_response_time_ms = self.p99_response_time_ms

        requests_per_second = self.requests_per_second

        error_rate_percent = self.error_rate_percent

        database_connections = self.database_connections

        redis_memory_usage_mb = self.redis_memory_usage_mb

        background_task_queue_size = self.background_task_queue_size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "avg_response_time_ms": avg_response_time_ms,
                "p95_response_time_ms": p95_response_time_ms,
                "p99_response_time_ms": p99_response_time_ms,
                "requests_per_second": requests_per_second,
                "error_rate_percent": error_rate_percent,
                "database_connections": database_connections,
                "redis_memory_usage_mb": redis_memory_usage_mb,
                "background_task_queue_size": background_task_queue_size,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        avg_response_time_ms = d.pop("avg_response_time_ms")

        p95_response_time_ms = d.pop("p95_response_time_ms")

        p99_response_time_ms = d.pop("p99_response_time_ms")

        requests_per_second = d.pop("requests_per_second")

        error_rate_percent = d.pop("error_rate_percent")

        database_connections = d.pop("database_connections")

        redis_memory_usage_mb = d.pop("redis_memory_usage_mb")

        background_task_queue_size = d.pop("background_task_queue_size")

        performance_metrics_response = cls(
            avg_response_time_ms=avg_response_time_ms,
            p95_response_time_ms=p95_response_time_ms,
            p99_response_time_ms=p99_response_time_ms,
            requests_per_second=requests_per_second,
            error_rate_percent=error_rate_percent,
            database_connections=database_connections,
            redis_memory_usage_mb=redis_memory_usage_mb,
            background_task_queue_size=background_task_queue_size,
        )

        performance_metrics_response.additional_properties = d
        return performance_metrics_response

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
