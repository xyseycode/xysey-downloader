import os
import msvcrt
import subprocess
import threading
import time

from pathlib import Path
from aria2.client import Aria2Client
from downloads.manager import DownloadManager



def start_aria2():
    """Start the aria2 RPC server with session recovery."""

    project_root = Path(__file__).resolve().parents[1]
    session_file = project_root / "aria2.session"
    session_file.touch(exist_ok=True)

    process = subprocess.Popen(
        [
            "aria2c",
            "--enable-rpc",
            "--rpc-listen-all=false",
            "--rpc-listen-port=6800",
            "--save-session=" + str(session_file),
            "--save-session-interval=30",
            "--auto-save-interval=5",
            "--input-file=" + str(session_file),
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

def print_downloads(manager):
    downloads = manager.all()

    if not downloads:
        print("\nNo downloads.")
        return
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

def view_download_details(manager):
    gid = input("\nEnter GID to view details: ").strip()

    download = manager.get(gid)

    if not download:
        print("\nDownload not found.")
        return

    # Refresh the download's latest information.
    download = manager.update(gid)

    if not download:
        print("\nDownload not found.")
        return

    print("\nDownload Details")
    print("================")
    print(f"GID:           {download.gid}")
    print(f"Filename:      {download.filename}")
    print(f"Status:        {download.status}")
    print(f"Progress:      {download.progress:.2f}%")
    print(f"Total size:    {format_bytes(download.total_size)}")
    print(f"Downloaded:    {format_bytes(download.completed_size)}")
    print(f"Speed:         {format_bytes(download.speed)}/s")
    print(f"ETA:           {download.eta}")

    if download.error_code != "0":
        print(f"Error code:    {download.error_code}")
        print(f"Error message: {download.error_message}")

    input("\nPress Enter to return to the menu...")

def monitor_downloads(manager, stop_event):
    while not stop_event.is_set():
        print_downloads(manager)
        time.sleep(1)

def watch_downloads(manager):
    while True:
        os.system("cls")
        print("Xysey Downloader - Live Monitor")
        print("===============================")
        print("Press Q to return to the menu.\n")

        print_downloads(manager)

        start_time = time.monotonic()

        while time.monotonic() - start_time < 1:
            if msvcrt.kbhit():
                key = msvcrt.getwch()

                if key.lower() == "q":
                    return

            time.sleep(0.05)



def main():

    # Create our aria2 client
    client = Aria2Client()
    manager = DownloadManager(client)
    manager.load_history()
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
            print("5. Remove Download")
            print("6. Exit")
            print("7. Watch downloads live")
            print("8. View download details")

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
                print_downloads(manager)

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
                gid = input("\nEnter GID to remove: ").strip()
                download = manager.get(gid)

                if not download:
                    print("\nDownload not found.")
                    continue

                manager.remove(gid)
                print("\nDownload removed.")


            elif choice == "6":
                print("\nExiting...")
                break

            elif choice == "7":
                watch_downloads(manager)

            elif choice == "8":
                view_download_details(manager)

            else:
                print("\nInvalid option.")

    finally:
        print("\nSaving download session...")

        try:
            client._rpc_call("aria2.saveSession")
            print("Download session saved.")

        except Exception as error:
            print(f"Could not save session: {error}")

        print("\nStopping aria2...")

        try:
            client._rpc_call("aria2.shutdown")
            aria2_process.wait(timeout=10)
            print("aria2 stopped gracefully.")

        except Exception as error:
            print(f"Graceful shutdown failed: {error}")

            if aria2_process.poll() is None:
                aria2_process.terminate()
                aria2_process.wait()


if __name__ == "__main__":
    main()
