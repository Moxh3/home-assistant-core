"""Manages the fetching of battery data."""

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .battery_monitor import ByteWattBatteryMonitor
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ByteWattDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Neovolt Battery data."""

    def __init__(
        self,
        hass: HomeAssistant,
        battery_monitor: ByteWattBatteryMonitor,
        update_interval: int,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval),
        )
        self.battery_monitor = battery_monitor

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            return await self.battery_monitor.get_battery_data()
        except UpdateFailed as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
