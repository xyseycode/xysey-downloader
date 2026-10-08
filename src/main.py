import subprocess
import time

from aria2.client import Aria2Client
from downloads.manager import DownloadManager


def start_aria2():
    """Start the aria2 RPC server."""

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


def wait_for_aria2(client):
    """Wait until aria2's RPC server is ready."""

    print("Starting aria2....")

    for _ in range(20):
        try:
            client.get_version()
            print("aria2 RPC is ready!")
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
    manager = DownloadManager(client)

    # start aria2
    aria2_process = start_aria2()

    try:
        # wait until aria2 is ready
        wait_for_aria2(client)

        while True:
            print("\n")
            print("Xysey Downloader")
            print("================")
            print("1. Add download")
            print("2. List downloads")
            print("3. Pause Download")
            print("4. Resume Download")
            print("5. Exit")

            choice = input("\nChoose an option: ").strip()

            if choice == "1":
                url = input("\nEnter download URL: ").strip()

                if not url:
                    print("No URL provided.")
                    continue
                if not url.startswith(("http://", "https://", "ftp://")):
                    print("Invalid URL.")
                    continue

                download = manager.add(url)

                print("\nDownload added!")
                print(f"GID: {download.gid}")

            elif choice == "2":
                downloads = manager.all()

                if not downloads:
                    print("\nNo downloads.")
                    continue
                # downloads table ui
                rows = []

                for download in downloads:
                    download = manager.update(download.gid)

                    rows.append(
                        [
                            download.gid,
                            download.filename,
                            f"{download.progress:.2f}%",
                            f"{format_bytes(download.speed)}/s",
                            download.status,
                        ]
                    )

                headers = [
                    "GID",
                    "File",
                    "Progress",
                    "Speed",
                    "Status",
                ]

                column_widths = []

                for column in zip(headers, *rows):
                    width = max(len(str(value)) for value in column)
                    column_widths.append(width)

                header = " ".join(
                    f"{header:<{width}}"
                    for header, width in zip(headers, column_widths)
                )

                print("\nDownloads")
                print("---------")
                print(header)
                print("-" * len(header))

                for row in rows:
                    print(
                        " ".join(
                            f"{value:<{width}}"
                            for value, width in zip(row, column_widths)
                        )
                    )

            elif choice == "3":
                gid = input("\nEnter GID to pause: ").strip()

                download = manager.get(gid)

                if not download:
                    print("\nDownload not found.")
                    continue

                manager.pause(gid)
                print("\nDownload paused.")

            elif choice == "4":
                gid = input("\nEnter GID to resume: ").strip()
                download = manager.get(gid)

                if not download:
                    print("\nDownload not found.")
                    continue

                manager.resume(gid)
                print("\nDownload resumed.")

            elif choice == "5":
                print("\nExiting...")
                break

            else:
                print("\nInvalid option.")

    finally:
        print("\nStopping aria2...")
        aria2_process.terminate()
        aria2_process.wait()


if __name__ == "__main__":
    main()
