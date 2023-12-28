"""The iRacing integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DATA_CONFIG_ENTRY
from .coordinator import IracingDataUpdateCoordinator

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iRacing from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_CONFIG_ENTRY, {})

    credsAvailable = (
        hass.data.get(DOMAIN, {})
        .get(DATA_CONFIG_ENTRY, {})
        .get("credentials_available", False)
    )
    if not credsAvailable:
        hass.data[DOMAIN][DATA_CONFIG_ENTRY]["username"] = entry.data["username"]
        hass.data[DOMAIN][DATA_CONFIG_ENTRY]["password"] = entry.data["password"]
        hass.data[DOMAIN][DATA_CONFIG_ENTRY]["credentials_available"] = True

    coordinator = IracingDataUpdateCoordinator(hass, entry, hass.data[DOMAIN][DATA_CONFIG_ENTRY]["username"], hass.data[DOMAIN][DATA_CONFIG_ENTRY]["password"])

    hass.data[DOMAIN][DATA_CONFIG_ENTRY][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN][DATA_CONFIG_ENTRY].pop(entry.entry_id)

    return unload_ok
