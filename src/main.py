import subprocess
import time

from aria2.client import Aria2Client


def start_aria2():
    """Start the aria2 RPC server."""

    process = subprocess.Popen(
        [
            "aria2c",
            "--enable-rpc",
            "--rpc-listen-all=false",
            "--rpc-listen-port=6800",
        ]
    )

    return process


def wait_for_aria2(client):
    """Wait until aria2's RPC server is ready."""

    print("Starting aria2....")

    for _ in range(20):
        try:
            client.get_version()
            print("aria2 RPC is read!")
            return

        except Exception:
            time.sleep(0.25)

    raise RuntimeError("Could not connect to aria2 RPC.")


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

    # Create our aria2 client
    client = Aria2Client()

    # start aria2
    aria2_process = start_aria2()

    try:
        # wait until aria2 is ready
        wait_for_aria2(client)

        # ask the user for a url
        url = input("\nEnter download URL: ").strip()

        if not url:
            print("No URL provided.")
            return

        # Tell aria2 to download it
        gid = client.add_download(url)

        print("\nDownload started!")
        print(f"GID: {gid}\n")

        # Monitor the download
        while True:
            status = client.get_status(gid)

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
                print("\n\nDownload failed!")
                break

            if state == "removed":
                print("\n\nDownload removed!")
                break

            time.sleep(0.5)

    finally:
        print("\nStopping aria2...")

        aria2_process.terminate()
        aria2_process.wait()


if __name__ == "__main__":
    main()
