import base64
import hashlib
import time
from datetime import datetime, timedelta

import requests


class irDataClient:
    def __init__(self, username=None, password=None, logger=None):
        self.authenticated = False
        self.session = requests.Session()
        self.base_url = "https://members-ng.iracing.com"

        self.username = username
        self.encoded_password = self._encode_password(username, password)
        self.car_names = {}
        self.authenticating = False
        self.logger = logger

    def log_error(self, message):
        if self.logger:
            self.logger.error(message)

    def log_info(self, message):
        if self.logger:
            self.logger.info(message)

    def _encode_password(self, username, password):
        initial_hash = hashlib.sha256(
            (password + username.lower()).encode("utf-8")
        ).digest()

        return base64.b64encode(initial_hash).decode("utf-8")

    def check_connection(self):
        self._login()

    def _login(self):
        headers = {"Content-Type": "application/json"}
        data = {"email": self.username, "password": self.encoded_password}
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
                "https://members-ng.iracing.com/auth",
                headers=headers,
                json=data,
                timeout=5.0,
            )
        except requests.Timeout:
            raise IracingConnectionError("Login timed out")
        except requests.ConnectionError:
            raise IracingConnectionError("Connection error")
        else:
            response_data = r.json()
            if r.status_code == 200 and response_data.get("authcode"):
                self.authenticated = True
                self.authenticating = False
                self._get_assets()
                self.log_info("Successful login")
            else:
                self.log_error("Failed login, status: " + str(r.status_code))
                raise IracingAuthError("Error from iRacing: ", response_data)

    def _get_assets(self):
        self._cars()

    def _add_assets(self, objects, assets, id_key):
        for obj in objects:
            a = assets[str(obj[id_key])]
            for key in a.keys():
                obj[key] = a[key]
        return objects

    def _cars(self):
        cars = self.get_cars()
        for car in cars:
            self.car_names[car["car_id"]] = car["car_name"]

    def _get_resource_or_link(self, url, params=None):
        if not self.authenticated:
            self._login()
            return self._get_resource_or_link(url, params=params)

        r = self.session.get(url, params=params)

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
        if not isinstance(data, list) and "link" in data.keys():
            return [data.get("link"), True]
        else:
            return [data, False]

    def _get_resource(self, endpoint, params=None):
        request_url = self._build_url(endpoint)
        resource_obj, is_link = self._get_resource_or_link(request_url, params=params)
        if not is_link:
            return resource_obj
        r = self.session.get(resource_obj)
        if r.status_code != 200:
            raise RuntimeError("Unhandled Non-200 response", r)
        return r.json()

    def _build_url(self, endpoint):
        return self.base_url + endpoint

    def get_member(self, cust_id, include_licenses=True):
        params = {"cust_ids": cust_id, "include_licenses": include_licenses}
        return self._get_resource("/data/member/get", params=params)

    def get_member_career(self, cust_id):
        params = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_career", params=params)

    def get_cars(self):
        return self._get_resource("/data/car/get")

    def get_recent_results(self, cust_id):
        params = {"cust_id": cust_id}
        results = self._get_resource("/data/stats/member_recent_races", params=params)
        for i, v in enumerate(results["races"]):
            results["races"][i]["car_name"] = self.car_names[v["car_id"]]
        return results


class IracingConnectionError(Exception):
    pass


class IracingAuthError(Exception):
    pass
