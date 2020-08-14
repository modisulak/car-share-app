import subprocess
from tests.user_face_data import face_encoding_json_str
import time

if __name__ == "__main__":
    p = subprocess.Popen(
        ["python3", "./agent_pi/face_recog.py", "1", face_encoding_json_str])
    while True:
        time.sleep(999999)
