from blogyourway.services.mongo import my_database
from datetime import datetime, timedelta


class CollectMetricData:
    def __init__(self, username: str, start_time: datetime, end_time: datetime) -> None:
        self._username = username
        self._start_time = start_time
        self._end_time = end_time

    def total_uv(self) -> int:
        total_uv = my_database.user_views.count_documents({"username": self._username})
        total_uv = format(total_uv, ",")
        return total_uv

    def total_pv(self) -> int:
        documents = my_database.user_views.find({"username": self._username})
        total_pv = 0
        for document in documents:
            total_pv += document["count"]
        total_pv = format(total_pv, ",")
        return total_pv

    def site_traffic(self) -> dict:
        data = {"labels": [], "data": []}
        current_query_time = self._start_time
        while current_query_time <= self._end_time:
            data["labels"].append(current_query_time.strftime("%b %d"))
            timestamp_str = current_query_time.strftime("%Y-%m-%d")
            count = my_database.metrics_log.count_documents(
                {
                    "username": self._username,
                    "type": "site_traffic",
                    "timestamp_str": timestamp_str,
                }
            )
            data["data"].append(count)
            current_query_time += timedelta(days=1)

        return data

    def index_pages_traffic(self) -> dict:
        data = {}
        records = my_database.metrics_log.find(
            {
                "username": self._username,
                "timestamp": {"$lte": self._end_time, "$gte": self._start_time},
                "type": "index_page_traffic",
            }
        )
        for record in records:
            if record["page"] not in data.keys():
                data[record["page"]] = 1
            else:
                data[record["page"]] += 1

        for page, views in data.items():
            data[page] = format(views, ",")

        return data
