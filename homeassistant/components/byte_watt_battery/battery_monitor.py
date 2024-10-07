"""Battery monitor for Neovolt Home Battery integration."""

import asyncio
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from . import helpers

_LOGGER = logging.getLogger(__name__)

# Define constants for timeouts
REQUEST_TIMEOUT = 5  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


class ByteWattBatteryMonitor:
    """A class to monitor Byte Watt Battery data.

    This class handles authentication, data retrieval, and caching for Byte Watt Battery systems.

    Attributes
    ----------
    username : str
        The username for authentication.
    password : str
        The password for authentication.
    auth_signature : str
        The authentication signature required for login.
    scan_interval : int
        The interval (in minutes) between data updates.
    access_token : str or None
        The current access token for API requests.
    last_update : datetime or None
        The timestamp of the last successful data update.
    battery_data : dict or None
        The most recently retrieved battery data.

    """

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        scan_interval: str,
    ) -> None:
        """Initialize the ByteWattBatteryMonitor.

        Parameters
        ----------
        hass : HomeAssistant
            The Home Assistant Root Object.
        username : str
            The username for authentication.
        password : str
            The password for authentication.
        scan_interval : int
            The interval (in minutes) between data updates.
        auth_signature : str
            The authentication signature required for login.
        auth_timestamp: str
            The timestamp of when the authentication signature was created.

        """
        self.hass = hass
        self.username = username
        self.password = password
        self.scan_interval = scan_interval
        self.auth_timestamp = helpers.generate_auth_timestamp()
        self.auth_signature = helpers.generate_auth_signature(self.auth_timestamp)
        self.access_token = None
        self.session = async_get_clientsession(hass)

    async def post_json_and_fetch_response(self, url, params, headers, payload):
        """Send a POST request and return response."""
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with self.session.post(
            url, params=params, headers=headers, json=payload, timeout=timeout
        ) as response:
            return await response.json()

    async def authenticate(self):
        """Authenticate with the Byte Watt API and obtain an access token.

        This method sends a request to the login endpoint with the user's credentials
        and stores the returned access token for future API requests.

        """
        url = "https://monitor.byte-watt.com/api/Account/Login"
        params = {
            "authsignature": self.auth_signature,
            "authtimestamp": self.auth_timestamp,
        }
        headers = {
            "Content-Type": "application/json",
        }
        payload = {"username": self.username, "password": self.password}

        try:
            data = await self.post_json_and_fetch_response(
                url, params, headers, payload
            )
            self.access_token = data["data"]["AccessToken"]
        except Exception as err:
            _LOGGER.error("Error during authentication: %s", err)
            raise UpdateFailed("Error authenticating with Byte Watt API") from err

    async def fetch_battery_data(self, url, params, headers) -> dict[str, Any]:
        """Send a GET request and return the JSON response body.

        This method sends a GET request to the API endpoint to fetch the latest power data.
        If the access token has expired, it will re-authenticate before retrying the request.

        """
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with self.session.get(
            url, params=params, headers=headers, timeout=timeout
        ) as response:
            if response.status == 401:
                _LOGGER.info("Token expired, re-authenticating and trying again")
                await self.authenticate()
                headers["Authorization"] = f"Bearer {self.access_token}"
                return {}  # Return empty dict to indicate need for retry

            data = await response.json()

            if data.get("code") == 9007:
                raise UpdateFailed("Network error code 9007 from Byte Watt API")

            if (
                "data" in data
                and isinstance(data["data"], dict)
                and len(data["data"]) > 0
            ):
                return data["data"]

            raise UpdateFailed("Unexpected data format from Byte Watt API")

    async def get_battery_data(self) -> dict[str, Any]:
        """Retrieve the latest battery data from the Byte Watt API.

        The retrieved data is stored in the `battery_data` attribute and the `last_update`
        timestamp is updated.

        Raises
        ------
        requests.exceptions.RequestException
            If the API request fails.

        """
        if not self.access_token:
            await self.authenticate()

        url = "https://monitor.byte-watt.com/api/ESS/GetLastPowerDataBySN"
        params = {
            "sys_sn": "All",
            "noLoading": "true",
        }
        headers = {
            "Content-Type": "application/json",
            "authtimestamp": str(self.auth_timestamp),
            "authsignature": self.auth_signature,
            "Authorization": f"Bearer {self.access_token}",
        }

        for attempt in range(MAX_RETRIES):
            try:
                data = await self.fetch_battery_data(url, params, headers)

                if data is not None:
                    return data

            except UpdateFailed as err:
                warning = f"UpdateFailed on attempt {attempt + 1}: {err}"
                _LOGGER.warning(warning)
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    raise
            except Exception as err:
                error = f"Error during API request on attempt {attempt + 1}: {err}"
                _LOGGER.error(error)
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    raise UpdateFailed(
                        "Error fetching data from Byte Watt API"
                    ) from err
        return {}  # Return empty dict if all retries fail
