"""Lightweight client for the iRacing public member API.

This module provides ``irDataClient`` which handles authentication and
convenience methods to fetch member details, career stats, cars and
recent race results from the iRacing members API.
"""

import base64
from datetime import datetime
import hashlib
import time

import requests
from requests.adapters import HTTPAdapter


class irDataClient:
    """Client for iRacing member API endpoints.

    The client manages a requests ``Session``, handles login and provides
    helper methods to fetch member data.
    """

    def __init__(
        self,
        username=None,
        password=None,
        client_id=None,
        client_secret=None,
        logger=None,
    ) -> None:
        """Initialize the client.

        Args:
            username: iRacing account email
            password: account password (plain text — will be encoded)
            logger: optional logger to forward informational and error logs
        """
        self.authenticated = False
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=30, pool_maxsize=30)
        self.session.mount("https://", adapter)

        self.base_url = "https://members-ng.iracing.com"
        self.oauth_url = "https://oauth.iracing.com/oauth2/token"

        self.username = username
        self.encoded_password = self._encode_password(username, password)
        self.client_id = client_id
        self.encoded_client_secret = self._encode_password(client_id, client_secret)
        self.car_names = {}
        self.authenticating = False
        self.logger = logger
        self.token = None
        self.refresh_token = None
        self.token_expires_in = None
        self.refresh_token_expires_in = None

    def log_error(self, message):
        """Log an error message via the optional logger."""
        if self.logger:
            self.logger.error(message)

    def log_info(self, message):
        """Log an informational message via the optional logger."""
        if self.logger:
            self.logger.info(message)

    def _encode_password(self, username, password):
        initial_hash = hashlib.sha256(
            (password + username.lower()).encode("utf-8")
        ).digest()

        return base64.b64encode(initial_hash).decode("utf-8")

    def check_connection(self):
        """Check that the client can authenticate with the iRacing API.

        This will attempt a login and raise on failure.
        """
        self._login()

    def _login(self):
        headers = {
            "Content-Type": "x-www-form-urlencoded",
            "Accept": "application/json",
        }
        data = {
            "username": self.username,
            "password": self.encoded_password,
            "grant_type": "password_limited",
            "client_id": self.client_id,
            "client_secret": self.encoded_client_secret,
            "scope": "iracing.auth",
        }
        if self.authenticating:
            self.log_info("Authenticating in progress, waiting")

            for _ in range(10):
                time.sleep(2)
                if not self.authenticating:
                    self.log_info("Authenticating done, continuing")
                    break

        if self.authenticated:
            return
        try:
            self.authenticating = True
            r = self.session.post(
                self.oauth_url,
                headers=headers,
                data=data,
                timeout=5.0,
            )
        except requests.Timeout as err:
            raise IracingConnectionError("Login timed out") from err
        except requests.ConnectionError as err:
            raise IracingConnectionError("Connection error") from err

        response_data = r.json()
        if r.status_code == 200 and response_data.get("access_token"):
            self.authenticated = True
            self.authenticating = False
            self.token = response_data.get("access_token")
            self.refresh_token = response_data.get("refresh_token")
            self.token_expires_in = response_data.get("expires_in", 0)
            self.refresh_token_expires_in = response_data.get(
                "refresh_token_expires_in", 0
            )

            # Preload car names mapping
            self._get_assets()
            self.log_info("Successful login")
        else:
            self.log_error("Failed login, status: " + str(r.status_code))
            raise IracingAuthError(f"Error from iRacing: {response_data}")

    def _get_assets(self):
        self._cars()

    def _add_assets(self, objects, assets, id_key):
        for obj in objects:
            a = assets[str(obj[id_key])]
            for key, val in a.items():
                obj[key] = val
        return objects

    def _cars(self):
        cars = self.get_cars()
        for car in cars:
            self.car_names[car["car_id"]] = car["car_name"]

    def _get_resource_or_link(self, url, params=None):
        if not self.authenticated or self.token is None:
            self._login()
            return self._get_resource_or_link(url, params=params)

        headers = {"Authorization": "Bearer " + self.token}

        r = self.session.get(url, params=params, headers=headers)

        if r.status_code == 401:
            # unauthorised, likely due to a timeout, retry after a login
            self.authenticated = False
            return self._get_resource_or_link(url, params=params)

        if r.status_code == 429:
            self.log_info("Rate limited, waiting...")

            ratelimit_reset = r.headers.get("x-ratelimit-reset")
            if ratelimit_reset:
                reset_datetime = datetime.fromtimestamp(int(ratelimit_reset))
                delta = reset_datetime - datetime.now()
                if delta.total_seconds() > 0:
                    time.sleep(delta.total_seconds())
            self.log_info("Rate limited, end of wait")
            return self._get_resource_or_link(url, params=params)

        if r.status_code != 200:
            self.log_error("API for " + url + "answsered " + str(r.status_code))

            raise RuntimeError("Unhandled Non-200 response", r)
        data = r.json()
        r.close()
        if not isinstance(data, list) and "link" in data:
            return [data.get("link"), True]

        return [data, False]

    def _get_resource(self, endpoint, params=None):
        request_url = self._build_url(endpoint)
        resource_obj, is_link = self._get_resource_or_link(request_url, params=params)
        if not is_link:
            return resource_obj
        r = self.session.get(resource_obj)
        r.close()
        if r.status_code != 200:
            raise RuntimeError("Unhandled Non-200 response", r)
        return r.json()

    def _build_url(self, endpoint):
        return self.base_url + endpoint

    def get_member(self, cust_id, include_licenses=True):
        """Return member information for the given customer id.

        Args:
            cust_id: customer id to query
            include_licenses: whether to include license information
        """
        params = {"cust_ids": cust_id, "include_licenses": include_licenses}
        return self._get_resource("/data/member/get", params=params)

    def get_member_career(self, cust_id):
        """Return career statistics for the given customer id."""
        params = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_career", params=params)

    def get_cars(self):
        """Return the available cars mapping from the API."""
        return self._get_resource("/data/car/get")

    def get_recent_results(self, cust_id):
        """Return recent race results for the given customer id.

        The method will annotate each result with a ``car_name`` using the
        cached ``car_names`` mapping populated by :meth:`_cars`.
        """
        params = {"cust_id": cust_id}
        results = self._get_resource("/data/stats/member_recent_races", params=params)
        for i, v in enumerate(results["races"]):
            results["races"][i]["car_name"] = self.car_names[v["car_id"]]
        return results


class IracingConnectionError(Exception):
    """Raised when the client cannot connect to the iRacing API."""


class IracingAuthError(Exception):
    """Raised when authentication with iRacing fails."""
