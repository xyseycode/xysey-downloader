from aria2.client import Aria2Client
from downloads.models import Download


class DownloadManager:

    def __init__(self, client):
        self.client = client
        self.downloads = {}

    def add(self, url):
        gid = self.client.add_download(url)

        download = Download(
            gid=gid,
            filename="Unknown",
            status="waiting",
        )

        self.downloads[gid] = download

        return download

    def update(self, gid):
        download = self.client.get_status(gid)

        self.downloads[gid] = download

        return download

    def get(self, gid):
        return self.downloads.get(gid)

    def all(self):
        return list(self.downloads.values())
