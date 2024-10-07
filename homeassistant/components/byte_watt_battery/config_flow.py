"""Config flow for Bytewatt Battery integration."""

from __future__ import annotations

from typing import Any

import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .battery_monitor import ByteWattBatteryMonitor
from .const import CONF_SCAN_INTERVAL, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=5): vol.All(
            vol.Coerce(int), vol.Range(min=1)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.

    Parameters
    ----------
    hass : HomeAssistant
        The Home Assistant instance.
    data : dict[str, Any]
        The user input data to validate.

    Returns
    -------
    dict[str, str]
        A dictionary containing the title for the config entry.

    Raises
    ------
    InvalidAuth
        If the authentication fails.

    """

    battery_monitor = ByteWattBatteryMonitor(
        hass,
        data["username"],
        data["password"],
        data[CONF_SCAN_INTERVAL],
    )

    try:
        # await hass.async_add_executor_job(battery_monitor.authenticate)
        await battery_monitor.authenticate()
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 401:
            raise InvalidAuth from err
        raise CannotConnect from err
    except requests.exceptions.RequestException as err:
        raise CannotConnect from err

    # If we get here, authentication was successful
    return {
        "title": f"Neovolt Battery ({data['username']})",
    }


class ByteWattBatteryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Byte Watt Battery."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step.

        Parameters
        ----------
        user_input : dict[str, Any] | None, optional
            The user input, by default None

        Returns
        -------
        FlowResult
            The result of the flow step.

        """
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_import(
        self, import_config: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle import from configuration.yaml.

        Parameters
        ----------
        import_config : dict[str, Any]
            The imported configuration.

        Returns
        -------
        FlowResult
            The result of the flow step.

        """
        return await self.async_step_user(import_config)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
