import json
import os
import urllib.request

from downloads.models import Download


class Aria2Client:
    def __init__(self, rpc_url="http://127.0.0.1:6800/jsonrpc"):
        self.rpc_url = rpc_url

    def _rpc_call(self, method, params=None):
        request_data = {
            "jsonrpc": "2.0",
            "id": "xysey-downloader",
            "method": method,
            "params": params or [],
        }

        data = json.dumps(request_data).encode("utf-8")

        request = urllib.request.Request(
            self.rpc_url,
            data=data,
            headers={
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))

    def get_version(self):
        return self._rpc_call("aria2.getVersion")

    def add_download(self, url, download_dir="downloads"):
        response = self._rpc_call(
            "aria2.addUri",
            [
                [url],
                {
                    "dir": download_dir,
                },
            ],
        )

        return response["result"]

    def get_status(self, gid):
        response = self._rpc_call(
            "aria2.tellStatus",
            [
                gid,
                [
                    "status",
                    "totalLength",
                    "completedLength",
                    "downloadSpeed",
                    "eta",
                    "files",
                ],
            ],
        )

        data = response["result"]
        files = data.get("files", [])
        if files:
            filename = os.path.basename(files[0]["path"])
        else:
            filename = "Unknown"

        return Download(
            gid=gid,
            filename=filename,
            status=data.get("status", "unknown"),
            total_size=int(data.get("totalLength", 0)),
            completed_size=int(data.get("completedLength", 0)),
            speed=int(data.get("downloadSpeed", 0)),
            eta=data.get("eta", "N/A"),
        )

    def pause(self, gid):
        response = self._rpc_call(
            "aria2.pause",
            [gid],
        )

        return response["result"]

    def resume(self, gid):
        response = self._rpc_call(
            "aria2.unpause",
            [gid]
        )

        return response["result"]
