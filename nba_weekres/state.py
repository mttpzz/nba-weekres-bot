import errno
import json
import os
import time

DEFAULT_STATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "state.json")

# Sibling lock file used to serialize overlapping runs (e.g. cron + manual
# workflow_dispatch) that read/write state.json around the same time.
_LOCK_PATH = DEFAULT_STATE_PATH + ".lock"
_LOCK_TIMEOUT_SECONDS = 30


def _acquire_lock(lock_path):
    # os.O_CREAT | O_EXCL is atomic even across processes/OSes, so only one
    # runner can hold the lock at a time; the loser waits instead of racing.
    deadline = time.time() + _LOCK_TIMEOUT_SECONDS
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
            if time.time() >= deadline:
                # Stale lock from a crashed run: proceed rather than hang forever.
                return
            time.sleep(0.1)


def _release_lock(lock_path):
    try:
        os.remove(lock_path)
    except OSError:
        pass


def load_last_sent_date(path=DEFAULT_STATE_PATH):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Empty/truncated/conflict-marker state.json: treat as "no previous state"
        # instead of crashing the whole weekly run.
        return None
    if not isinstance(data, dict):
        # Valid JSON but not an object (e.g. null, [], "..."): no usable state.
        return None
    return data.get("last_sent_date")


def save_last_sent_date(date_str, path=DEFAULT_STATE_PATH):
    lock_path = path + ".lock" if path != DEFAULT_STATE_PATH else _LOCK_PATH
    _acquire_lock(lock_path)
    try:
        # Write to a temp file and rename so a crash mid-write can never leave
        # state.json truncated/corrupted for the next run to read.
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump({"last_sent_date": date_str}, f)
        os.replace(tmp_path, path)
    finally:
        _release_lock(lock_path)
