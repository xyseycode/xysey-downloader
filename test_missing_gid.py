
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from aria2.client import Aria2Client

client = Aria2Client()

try:
    client.get_status("nonexistent-test-gid")
except Exception as error:
    print(type(error).__name__)
    print(error)
