from dataclasses import dataclass


@dataclass
class Download:
    gid: str
    filename: str = "Unknown"
    status: str = "unknown"

    total_size: int = 0
    completed_size: int = 0
    speed: int = 0
    eta: str = "N/A"
    error_code: str = "0"
    error_message: str = ""

    @property
    def progress(self):
        if self.total_size == 0:
            return 0.0

        return self.completed_size / self.total_size * 100
