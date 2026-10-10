import json
from pathlib import Path

from aria2.client import Aria2Client
from aria2.client import DownloaderNotFoundError
from downloads.models import Download


class DownloadManager:
    def __init__(self, client):
        self.client = client
        self.downloads = {}

        project_root = Path(__file__).resolve().parents[2]
        self.history_file = project_root / "downloads.json"

    def save_history(self):
        data = []

        for download in self.downloads.values():
            data.append({
                "gid": download.gid,
                "filename": download.filename,
                "status": download.status,
                "total_size": download.total_size,
                "completed_size": download.completed_size,
                "speed": download.speed,
                "eta": download.eta,
                "error_code": download.error_code,
                "error_message": download.error_message,
            })

        with self.history_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def add(self, url):
        gid = self.client.add_download(url)

        download = Download(
            gid=gid,
            filename="Unknown",
            status="waiting",
        )

        self.downloads[gid] = download
        self.save_history()

        return download


    def update(self, gid):
        try:
            download = self.client.get_status(gid)
        except DownloaderNotFoundError:
            download = self.downloads.get(gid)

            if download:
               download.status = "unavailable"
               download.speed = 0
               download.eta = "N/A"
               self.save_history()

            return download

        self.downloads[gid] = download
        self.save_history()

        return download

    def get(self, gid):
        return self.downloads.get(gid)

    def all(self):
        return list(self.downloads.values())

    def pause(self, gid):
        self.client.pause(gid)

    def resume(self, gid):
        self.client.resume(gid)

    def remove(self, gid):
        self.client.remove(gid)
        self.downloads.pop(gid, None)
        self.save_history()

    def load_history(self):
        if not self.history_file.exists():
            return

        with self.history_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        for item in data:
            download = Download(
                gid=item["gid"],
                filename=item.get("filename", "Unknown"),
                status=item.get("status", "unknown"),
                total_size=item.get("total_size", 0),
                completed_size=item.get("completed_size", 0),
                speed=item.get("speed", 0),
                eta=item.get("eta", "N/A"),
                error_code=item.get("error_code", "0"),
                error_message=item.get("error_message", ""),
            )

            self.downloads[download.gid] = download
