"""White light schedule start/end time."""

from __future__ import annotations

from datetime import time as dt_time
from typing import Any

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ICSeeConfigEntry, ICSeeCoordinator
from .entity import ICSeeEntity, get_path

OTHER = "SystemFunction.OtherFunction."


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ICSeeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities: list[ICSeeEntity] = []
    if coordinator.ability(OTHER + "SupportCameraWhiteLight") and get_path(
        coordinator.channel_value("Camera.WhiteLight", 0), ("WorkPeriod",)
    ):
        entities += [
            WhiteLightStartTime(coordinator),
            WhiteLightEndTime(coordinator),
        ]
    async_add_entities(entities)


class _WhiteLightPeriodTime(ICSeeEntity, TimeEntity):
    """One end of Camera.WhiteLight.WorkPeriod (a start or end wall-clock time)."""

    _attr_entity_category = EntityCategory.CONFIG
    _hour_key: str
    _minute_key: str

    def __init__(self, coordinator: ICSeeCoordinator, key: str) -> None:
        super().__init__(coordinator, key, 0)
        self.entity_description = TimeEntityDescription(key=key, translation_key=key)

    @property
    def available(self) -> bool:
        return super().available and self._period is not None

    @property
    def _period(self) -> dict[str, Any] | None:
        return get_path(
            self.coordinator.channel_value("Camera.WhiteLight", self.channel),
            ("WorkPeriod",),
        )

    @property
    def native_value(self) -> dt_time | None:
        period = self._period
        if period is None:
            return None
        hour = period.get(self._hour_key)
        minute = period.get(self._minute_key)
        if hour is None or minute is None:
            return None
        return dt_time(hour=hour, minute=minute)

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.async_update_config(
            "Camera.WhiteLight",
            self.channel,
            lambda obj: obj["WorkPeriod"].update(
                {self._hour_key: value.hour, self._minute_key: value.minute}
            ),
        )


class WhiteLightStartTime(_WhiteLightPeriodTime):
    _hour_key = "SHour"
    _minute_key = "SMinute"

    def __init__(self, coordinator: ICSeeCoordinator) -> None:
        super().__init__(coordinator, "white_light_start")


class WhiteLightEndTime(_WhiteLightPeriodTime):
    _hour_key = "EHour"
    _minute_key = "EMinute"

    def __init__(self, coordinator: ICSeeCoordinator) -> None:
        super().__init__(coordinator, "white_light_end")
