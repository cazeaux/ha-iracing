import base64
import hashlib
import time
from datetime import datetime, timedelta

import requests


class irDataClient:
    def __init__(self, username=None, password=None):
        self.authenticated = False
        self.session = requests.Session()
        self.base_url = "https://members-ng.iracing.com"

        self.username = username
        self.encoded_password = self._encode_password(username, password)

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

        try:
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
                return "Logged in"
            else:
                raise IracingAuthError("Error from iRacing: ", response_data)

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
            print("Rate limited, waiting")
            ratelimit_reset = r.headers.get("x-ratelimit-reset")
            if ratelimit_reset:
                reset_datetime = datetime.fromtimestamp(int(ratelimit_reset))
                delta = reset_datetime - datetime.now()
                if delta.total_seconds() > 0:
                    time.sleep(delta.total_seconds())
            return self._get_resource_or_link(url, params=params)

        if r.status_code != 200:
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

    def get_recent_results(self, cust_id):
        params = {"cust_id": cust_id}
        return self._get_resource("/data/stats/member_recent_races", params=params)


class IracingConnectionError(Exception):
    pass


class IracingAuthError(Exception):
    pass
