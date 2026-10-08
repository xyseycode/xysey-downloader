import json
import subprocess
import time
import urllib.request


RPC_URL = "http://127.0.0.1:6800/jsonrpc"


def rpc_call(method, params=None):
    """Send a JSON-RPC request to aria2."""

    request_data = {
        "jsonrpc": "2.0",
        "id": "my-downloader",
        "method": method,
        "params": params or [],
    }

    data = json.dumps(request_data).encode("utf-8")

    request = urllib.request.Request(
        RPC_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def start_aria2():
    """Start aria2 with its RPC server enabled."""

    process = subprocess.Popen(
        [
            "aria2c",
            "--enable-rpc",
            "--rpc-listen-all=false",
            "--rpc-listen-port=6800",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return process


def wait_for_aria2():
    """Wait until aria2's RPC server is ready."""

    print("Starting aria2...")

    for _ in range(20):
        try:
            rpc_call("aria2.getVersion")
            print("aria2 RPC is ready!")
            return
        except Exception:
            time.sleep(0.25)

    raise RuntimeError("Could not connect to aria2 RPC.")


def add_download(url):
    """Tell aria2 to download a URL."""

    response = rpc_call(
        "aria2.addUri",
        [
            [url],
            {
                "dir": "downloads",
            },
        ],
    )

    return response["result"]


def get_status(gid):
    """Get the current status of a download."""

    response = rpc_call(
        "aria2.tellStatus",
        [
            gid,
            [
                "status",
                "totalLength",
                "completedLength",
                "downloadSpeed",
                "eta",
                "filename",
            ],
        ],
    )

    return response["result"]


def format_bytes(value):
    """Convert bytes into a human-readable string."""

    value = float(value)

    units = ["B", "KB", "MB", "GB", "TB"]

    for unit in units:
        if value < 1024:
            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{value:.2f} PB"


def main():

    # Start aria2
    aria2_process = start_aria2()

    try:
        # Wait until RPC is available
        wait_for_aria2()

        # URL to download
        url = input("\nEnter download URL: ").strip()

        if not url:
            print("No URL provided.")
            return

        # Add download
        gid = add_download(url)

        print(f"\nDownload started!")
        print(f"GID: {gid}\n")

        # Monitor download
        while True:

            status = get_status(gid)

            state = status["status"]

            total = int(status.get("totalLength", 0))
            completed = int(status.get("completedLength", 0))
            speed = int(status.get("downloadSpeed", 0))

            filename = status.get("filename", "Unknown")

            if total > 0:
                percentage = completed / total * 100
            else:
                percentage = 0

            print(
                f"\r"
                f"{filename} | "
                f"{percentage:6.2f}% | "
                f"{format_bytes(completed)} / "
                f"{format_bytes(total)} | "
                f"{format_bytes(speed)}/s",
                end="",
                flush=True,
            )

            if state == "complete":
                print("\n\nDownload complete!")
                break

            if state == "error":
                print("\n\nDownload failed.")
                break

            if state == "removed":
                print("\n\nDownload removed.")
                break

            time.sleep(0.5)

    finally:
        print("\nStopping aria2...")

        aria2_process.terminate()
        aria2_process.wait()


if __name__ == "__main__":
    main()
