"""Config flow for iRacing integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import requests
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from .iracingapi import irDataClient, IracingConnectionError, IracingAuthError
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.core import callback

from .const import DOMAIN, DATA_CONFIG_ENTRY

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
        ),
        vol.Required("password"): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
        vol.Required("cust_id"): TextSelector(
            TextSelectorConfig(type=TextSelectorType.NUMBER, autocomplete="12345")
        ),
    }
)

STEP_USER_DATA_SCHEMA_NO_LOGIN = vol.Schema(
    {
        vol.Required("cust_id"): TextSelector(
            TextSelectorConfig(type=TextSelectorType.NUMBER, autocomplete="12345")
        ),
    }
)

OPTIONS_STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
        ),
        vol.Required("password"): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


def validate_iracing_credentials(data) -> None:
    """Verify credentials"""
    client = irDataClient(data["username"], data["password"])
    client.check_connection()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iRacing."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        credsAvailable = (
            self.hass.data.get(DOMAIN, {})
            .get(DATA_CONFIG_ENTRY, {})
            .get("credentials_available", False)
        )
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                if not credsAvailable:
                    await self.hass.async_add_executor_job(
                        validate_iracing_credentials, user_input
                    )
                pass
            except IracingConnectionError:
                errors["base"] = "cannot_connect"
            except IracingAuthError as err:
                errors["base"] = "invalid_auth"
                # raise ConfigEntryAuthFailed from err
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input["cust_id"], data=user_input
                )

        if credsAvailable:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA_NO_LOGIN,
                errors=errors,
            )
        else:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(
                    validate_iracing_credentials, user_input
                )
            except IracingConnectionError:
                errors["base"] = "cannot_connect"
            except IracingAuthError as err:
                errors["base"] = "invalid_auth"
                # raise ConfigEntryAuthFailed from err
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=self.config_entry.data["cust_id"], data=user_input
                )

        return self.async_show_form(
            step_id="init", data_schema=OPTIONS_STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
