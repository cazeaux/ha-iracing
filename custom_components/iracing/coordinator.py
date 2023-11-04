"""Data update coordinator for the Pronote integration."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .iracingapi import irDataClient

from .const import DEFAULT_REFRESH_INTERVAL

_LOGGER = logging.getLogger(__name__)


def get_iracing_client(username, password) -> irDataClient | None:
    client = irDataClient(username, password)
    return client


class IracingDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for the iRacing integration."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, username: str, password: str
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=entry.title,
            update_interval=timedelta(
                minutes=entry.options.get("refresh_interval", DEFAULT_REFRESH_INTERVAL)
            ),
        )
        self.config_entry = entry
        self.username = username
        self.password = password

    async def _async_update_data(self) -> dict[Platform, dict[str, Any]]:
        """Get the latest data from iRacing and updates the state."""

        data = self.config_entry.data
        res = {
            "cust_id": data["cust_id"],
            "road_licence_ir": None,
            "road_licence_sr": None,
            "road_starts": None,
            "road_laps": None,
            "road_wins": None,
            "road_top5": None,
            "dirt_road_licence_ir": None,
            "dirt_road_licence_sr": None,
            "dirt_road_starts": None,
            "dirt_road_laps": None,
            "dirt_road_wins": None,
            "dirt_road_top5": None,
            "oval_licence_ir": None,
            "oval_licence_sr": None,
            "oval_starts": None,
            "oval_laps": None,
            "oval_wins": None,
            "oval_top5": None,
            "dirt_oval_licence_ir": None,
            "dirt_oval_licence_sr": None,
            "dirt_oval_starts": None,
            "dirt_oval_laps": None,
            "dirt_oval_wins": None,
            "dirt_oval_top5": None,
            "name": None,
        }

        client = await self.hass.async_add_executor_job(
            get_iracing_client, self.username, self.password
        )

        if client is None:
            _LOGGER.error("Unable to init iracing client")
            return None

        try:
            member_info = await self.hass.async_add_executor_job(
                client.get_member, data["cust_id"]
            )
            licence_road = next(
                x
                for x in member_info["members"][0]["licenses"]
                if x["category_id"] == 2
            )
            licence_dirt_road = next(
                x
                for x in member_info["members"][0]["licenses"]
                if x["category_id"] == 4
            )
            licence_oval = next(
                x
                for x in member_info["members"][0]["licenses"]
                if x["category_id"] == 1
            )
            licence_dirt_oval = next(
                x
                for x in member_info["members"][0]["licenses"]
                if x["category_id"] == 3
            )

            member_career = await self.hass.async_add_executor_job(
                client.get_member_career, data["cust_id"]
            )
            carrer_road = next(
                x for x in member_career["stats"] if x["category_id"] == 2
            )
            carrer_dirt_road = next(
                x for x in member_career["stats"] if x["category_id"] == 4
            )
            carrer_oval = next(
                x for x in member_career["stats"] if x["category_id"] == 1
            )
            carrer_dirt_oval = next(
                x for x in member_career["stats"] if x["category_id"] == 3
            )

            recent_results = await self.hass.async_add_executor_job(
                client.get_recent_results, data["cust_id"]
            )

            res["road_licence_ir"] = licence_road.get("irating", None)
            res["road_licence_sr"] = licence_road["safety_rating"]
            res["road_starts"] = carrer_road["starts"]
            res["road_laps"] = carrer_road["laps"]
            res["road_wins"] = carrer_road["wins"]
            res["road_top5"] = carrer_road["top5"]

            res["dirt_road_licence_ir"] = licence_dirt_road.get("irating", None)
            res["dirt_road_licence_sr"] = licence_dirt_road["safety_rating"]
            res["dirt_road_starts"] = carrer_dirt_road["starts"]
            res["dirt_road_laps"] = carrer_dirt_road["laps"]
            res["dirt_road_wins"] = carrer_dirt_road["wins"]
            res["dirt_road_top5"] = carrer_dirt_road["top5"]

            res["oval_licence_ir"] = licence_oval.get("irating", None)
            res["oval_licence_sr"] = licence_oval["safety_rating"]
            res["oval_starts"] = carrer_oval["starts"]
            res["oval_laps"] = carrer_oval["laps"]
            res["oval_wins"] = carrer_oval["wins"]
            res["oval_top5"] = carrer_oval["top5"]

            res["dirt_oval_licence_ir"] = licence_dirt_oval.get("irating", None)
            res["dirt_oval_licence_sr"] = licence_dirt_oval["safety_rating"]
            res["dirt_oval_starts"] = carrer_dirt_oval["starts"]
            res["dirt_oval_laps"] = carrer_dirt_oval["laps"]
            res["dirt_oval_wins"] = carrer_dirt_oval["wins"]
            res["dirt_oval_top5"] = carrer_dirt_oval["top5"]

            res["name"] = member_info["members"][0]["display_name"]
            res["recent_results"] = {"recent_results": recent_results["races"][:5]}

        except Exception as ex:
            _LOGGER.info("Error getting member info from iracing: %s", ex)

        return res
