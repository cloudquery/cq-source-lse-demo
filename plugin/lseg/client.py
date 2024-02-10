from csv import DictReader
from datetime import datetime, time, timedelta
from typing import Generator, Dict, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests import Session


class LSEGClient:
    def __init__(
        self, username: str, password: str, base_url="https://dmd.lseg.com/dmd/"
    ):
        self._base_url = base_url
        self._username = username
        self._password = password
        self._session = self.__login()

    def __login(self):
        session = Session()
        login_page = session.get(urljoin(self._base_url, "login.html"))
        login_soup = BeautifulSoup(login_page.content, "html.parser")
        csrf_token = login_soup.form.find("input", type="hidden")["value"]
        result = session.post(
            urljoin(self._base_url, "login.html"),
            data={
                "username": self._username,
                "password": self._password,
                "_csrf": csrf_token,
            },
        )
        result.raise_for_status()
        return session

    def xlon_iterator(self) -> Generator[Dict[str, Any], None, None]:
        dir_path = urljoin(self._base_url, "download/posttrade/LSE/FCA/")
        end = datetime.combine(datetime.now().date(), time(16, 30))
        cursor = datetime.combine(end.date(), time(8, 0))
        if cursor.isoweekday() > 5:
            return
        while cursor < datetime.now() and cursor <= end:
            response = self._session.get(
                urljoin(
                    dir_path,
                    f"XLON-post-{cursor.year}-{cursor.month:02}-{cursor.day:02}T{cursor.hour:02}_{cursor.minute:02}.csv",
                )
            )
            response.raise_for_status()
            csv_file = response.content.decode()
            reader = DictReader(csv_file.splitlines(), delimiter=";")
            for row in reader:
                yield row
            cursor += timedelta(minutes=1)
