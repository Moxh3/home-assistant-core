"""Sensor platform for Byte Watt Battery integration."""

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ByteWattDataUpdateCoordinator


def get_power_value(data: dict[str, Any], key: str) -> float:
    """Safely get power value from data."""
    value = data.get(key)
    return float(value) if value is not None else 0.0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Byte Watt Battery sensor platform.

    Parameters
    ----------
    hass : HomeAssistant
        The Home Assistant instance.
    entry : ConfigEntry
        The config entry.
    async_add_entities : AddEntitiesCallback
        Callback to add new entities to Home Assistant.

    """

    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        BatterySensor(
            coordinator,
            "State of Charge",
            lambda data: data.get("soc"),
            PERCENTAGE,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.BATTERY,
        ),
        BatterySensor(
            coordinator,
            "Grid Phase 1 Feed-In",
            lambda data: abs(min(get_power_value(data, "pmeter_l1"), 0)),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Grid Phase 1 Consumption",
            lambda data: max(get_power_value(data, "pmeter_l1"), 0),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Grid Phase 2 Feed-In",
            lambda data: abs(min(get_power_value(data, "pmeter_l2"), 0)),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Grid Phase 2 Consumption",
            lambda data: max(get_power_value(data, "pmeter_l2"), 0),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Grid Phase 3 Feed-In",
            lambda data: abs(min(get_power_value(data, "pmeter_l3"), 0)),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Grid Phase 3 Consumption",
            lambda data: max(get_power_value(data, "pmeter_l3"), 0),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Battery Charging",
            lambda data: abs(min(get_power_value(data, "pbat"), 0)),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor.create_hidden(
            coordinator,
            "MPPT Tracker String 1",
            lambda data: data.get("ppv1"),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor.create_hidden(
            coordinator,
            "MPPT Tracker String 2",
            lambda data: data.get("ppv2"),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor.create_hidden(
            coordinator,
            "MPPT Tracker String 3",
            lambda data: data.get("ppv3"),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor.create_hidden(
            coordinator,
            "MPPT Tracker String 4",
            lambda data: data.get("ppv4"),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Battery Phase 1 Discharging",
            lambda data: data.get("preal_l1"),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Battery Phase 2 Discharging",
            lambda data: data.get("preal_l2"),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Battery Phase 3 Discharging",
            lambda data: data.get("preal_l3"),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Battery Discharging",
            lambda data: max(
                sum(get_power_value(data, f"preal_l{i}") for i in range(1, 4)), 0
            ),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "PV Generation",
            lambda data: sum(get_power_value(data, f"ppv{i}") for i in range(1, 5)),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Grid Feed-In",
            lambda data: abs(
                min(sum(get_power_value(data, f"pmeter_l{i}") for i in range(1, 4)), 0)
            ),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
        BatterySensor(
            coordinator,
            "Grid Consumption",
            lambda data: max(
                sum(get_power_value(data, f"pmeter_l{i}") for i in range(1, 4)), 0
            ),
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            SensorDeviceClass.POWER,
        ),
    ]

    async_add_entities(sensors, True)


class BatterySensor(CoordinatorEntity, SensorEntity):
    """Sensor entity for derived power values from Byte Watt Battery data."""

    def __init__(
        self,
        coordinator: ByteWattDataUpdateCoordinator,
        name: str,
        # formula: Callable[[dict], float],
        formula: Callable[[dict], int | float | Any | None],
        unit,
        state_class,
        device_class,
        entity_registry_enabled_default: bool = True,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._name = name
        self._formula = formula
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        self._attr_device_class = device_class
        self._attr_unique_id = f"{name.lower().replace(' ', '_')}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.battery_monitor.username)},
            "name": f"Neovolt Home Battery ({coordinator.battery_monitor.username})",
            "manufacturer": "Neovolt",
            "model": "Battery System",
        }
        self._attr_entity_registry_enabled_default = entity_registry_enabled_default

    @classmethod
    def create_hidden(
        cls,
        coordinator: ByteWattDataUpdateCoordinator,
        name: str,
        # formula: Callable[[dict], float],
        formula: Callable[[dict], int | float | Any | None],
        unit,
        state_class,
        device_class,
    ):
        """Create a hidden sensor."""
        return cls(
            coordinator,
            name,
            formula,
            unit,
            state_class,
            device_class,
            entity_registry_enabled_default=False,
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self) -> float | None:
        """Return the derived power value."""
        if self.coordinator.data:
            return self._formula(self.coordinator.data)
        return None
