import datetime
from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="SystemHealthResponse")


@_attrs_define
class SystemHealthResponse:
    """
    Attributes:
        status (str):
        timestamp (datetime.datetime):
        version (str):
        uptime_seconds (float):
        database_connected (bool):
        redis_connected (bool):
        celery_workers (int):
        memory_usage_mb (float):
        cpu_usage_percent (float):
    """

    status: str
    timestamp: datetime.datetime
    version: str
    uptime_seconds: float
    database_connected: bool
    redis_connected: bool
    celery_workers: int
    memory_usage_mb: float
    cpu_usage_percent: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        timestamp = self.timestamp.isoformat()

        version = self.version

        uptime_seconds = self.uptime_seconds

        database_connected = self.database_connected

        redis_connected = self.redis_connected

        celery_workers = self.celery_workers

        memory_usage_mb = self.memory_usage_mb

        cpu_usage_percent = self.cpu_usage_percent

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "timestamp": timestamp,
                "version": version,
                "uptime_seconds": uptime_seconds,
                "database_connected": database_connected,
                "redis_connected": redis_connected,
                "celery_workers": celery_workers,
                "memory_usage_mb": memory_usage_mb,
                "cpu_usage_percent": cpu_usage_percent,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = d.pop("status")

        timestamp = isoparse(d.pop("timestamp"))

        version = d.pop("version")

        uptime_seconds = d.pop("uptime_seconds")

        database_connected = d.pop("database_connected")

        redis_connected = d.pop("redis_connected")

        celery_workers = d.pop("celery_workers")

        memory_usage_mb = d.pop("memory_usage_mb")

        cpu_usage_percent = d.pop("cpu_usage_percent")

        system_health_response = cls(
            status=status,
            timestamp=timestamp,
            version=version,
            uptime_seconds=uptime_seconds,
            database_connected=database_connected,
            redis_connected=redis_connected,
            celery_workers=celery_workers,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
        )

        system_health_response.additional_properties = d
        return system_health_response

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
