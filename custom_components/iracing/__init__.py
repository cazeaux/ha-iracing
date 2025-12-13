"""The iRacing integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DATA_CONFIG_ENTRY, DOMAIN
from .coordinator import IracingDataUpdateCoordinator
from .iracingapi import irDataClient

# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)


def get_iracing_client(
    username, password, client_id, client_secret
) -> irDataClient | None:
    """Get an authenticated iRacing client."""
    return irDataClient(username, password, client_id, client_secret, _LOGGER)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iRacing from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_CONFIG_ENTRY, {})

    if "username" in entry.data:
        hass.data[DOMAIN][DATA_CONFIG_ENTRY]["username"] = entry.data["username"]
        hass.data[DOMAIN][DATA_CONFIG_ENTRY]["password"] = entry.data["password"]
        hass.data[DOMAIN][DATA_CONFIG_ENTRY]["client_id"] = entry.data["client_id"]
        hass.data[DOMAIN][DATA_CONFIG_ENTRY]["client_secret"] = entry.data[
            "client_secret"
        ]
        hass.data[DOMAIN][DATA_CONFIG_ENTRY]["credentials_available"] = True

        hass.data[DOMAIN][DATA_CONFIG_ENTRY]["api"] = get_iracing_client(
            entry.data["username"],
            entry.data["password"],
            entry.data["client_id"],
            entry.data["client_secret"],
        )

    coordinator = IracingDataUpdateCoordinator(
        hass,
        entry,
        hass.data[DOMAIN][DATA_CONFIG_ENTRY]["api"],
    )

    hass.data[DOMAIN][DATA_CONFIG_ENTRY][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN][DATA_CONFIG_ENTRY].pop(entry.entry_id)

    return unload_ok
