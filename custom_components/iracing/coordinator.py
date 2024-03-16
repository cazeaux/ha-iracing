"""Data update coordinator for the Pronote integration."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_REFRESH_INTERVAL

_LOGGER = logging.getLogger(__name__)


class IracingDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for the iRacing integration."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api) -> None:
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
        self.api = api

    async def _async_update_data(self) -> dict[Platform, dict[str, Any]]:
        """Get the latest data from iRacing and updates the state."""

        data = self.config_entry.data
        res = {
            "cust_id": data["cust_id"],
            "sports_car_licence_ir": None,
            "sports_car_licence_sr": None,
            "sports_car_starts": None,
            "sports_car_laps": None,
            "sports_car_wins": None,
            "sports_car_top5": None,
            "formula_car_licence_ir": None,
            "formula_car_licence_sr": None,
            "formula_car_starts": None,
            "formula_car_laps": None,
            "formula_car_wins": None,
            "formula_car_top5": None,
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

        client = self.api

        if client is None:
            _LOGGER.error("Unable to init iracing client")
            return None

        try:
            member_info = await self.hass.async_add_executor_job(
                client.get_member, data["cust_id"]
            )
            licence_sports_car = next(
                x
                for x in member_info["members"][0]["licenses"]
                if x["category_id"] == 5
            )
            licence_formula_car = next(
                x
                for x in member_info["members"][0]["licenses"]
                if x["category_id"] == 6
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
            carrer_sports_car = next(
                x for x in member_career["stats"] if x["category_id"] == 5
            )
            carrer_formula_car = next(
                x for x in member_career["stats"] if x["category_id"] == 6
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

            res["sports_car_licence_ir"] = licence_sports_car.get("irating", None)
            res["sports_car_licence_sr"] = licence_sports_car["safety_rating"]
            res["sports_car_starts"] = carrer_sports_car["starts"]
            res["sports_car_laps"] = carrer_sports_car["laps"]
            res["sports_car_wins"] = carrer_sports_car["wins"]
            res["sports_car_top5"] = carrer_sports_car["top5"]

            res["formula_car_licence_ir"] = licence_formula_car.get("irating", None)
            res["formula_car_licence_sr"] = licence_formula_car["safety_rating"]
            res["formula_car_starts"] = carrer_formula_car["starts"]
            res["formula_car_laps"] = carrer_formula_car["laps"]
            res["formula_car_wins"] = carrer_formula_car["wins"]
            res["formula_car_top5"] = carrer_formula_car["top5"]

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
