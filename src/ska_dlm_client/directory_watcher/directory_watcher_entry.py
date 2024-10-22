from pathlib import PosixPath

class DirectoryWatcherEntry():
    def __init__(self,
                 file_or_directory: PosixPath,
                 dlm_storage_id: str,
                 dlm_registration_id: str,
                 time_registered: float):
        directory_entry = file_or_directory
        dlm_storage_id = dlm_storage_id
        dlm_regsitration_id = dlm_registration_id
        time_registered = time_registered
