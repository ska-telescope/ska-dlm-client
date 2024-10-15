# This is expected to be replaced based on what final deployment looks like.

class dlm_configuration:
    SERVER = "http://localhost"
    DLM_ENTRY_POINTS = {
        "gateway":   8000,
        "ingest":    8001,
        "request":   8002,
        "storage":   8003,
        "migration": 8004
    }

class watcher_configuration:
    DIRECTORY_TO_WATCH = "a"
    STORAGE_ID_FOR_REGISTRATION = "b"
