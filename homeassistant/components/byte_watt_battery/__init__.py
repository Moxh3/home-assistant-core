"""The Neovolt Home Battery integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .battery_monitor import ByteWattBatteryMonitor
from .const import CONF_SCAN_INTERVAL, DOMAIN
from .coordinator import ByteWattDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Neovolt Home Battery component.

    Parameters
    ----------
    hass : HomeAssistant
        The Home Assistant instance.
    config : ConfigType
        The configuration.

    Returns
    -------
    bool
        True if setup was successful, False otherwise.

    """
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Neovolt Home Battery from a config entry.

    Parameters
    ----------
    hass : HomeAssistant
        The Home Assistant instance.
    entry : ConfigEntry
        The config entry.

    Returns
    -------
    bool
        True if setup was successful, False otherwise.

    """
    battery_monitor = ByteWattBatteryMonitor(
        hass,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_SCAN_INTERVAL, 30),
    )

    coordinator = ByteWattDataUpdateCoordinator(
        hass, battery_monitor, entry.data.get(CONF_SCAN_INTERVAL, 1)
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Parameters
    ----------
    hass : HomeAssistant
        The Home Assistant instance.
    entry : ConfigEntry
        The config entry to unload.

    Returns
    -------
    bool
        True if unload was successful, False otherwise.

    """
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
