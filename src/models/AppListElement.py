from typing import Optional, Dict
from enum import Enum

class InstalledStatus(Enum):
    INSTALLED = 1
    NOT_INSTALLED = 2
    UNINSTALLING = 3
    ERROR = 4
    UNKNOWN = 5
    INSTALLING = 6
    UPDATE_AVAILABLE = 7
    UPDATING = 8

class AppListElement():
    def __init__(self, name: str, description: str, app_id: str, provider: str, installed_status: InstalledStatus, size: float=None, **kwargs):
        self.name: str = name
        self.description: str = description
        self.id = app_id
        self.provider: str = provider
        self.installed_status: InstalledStatus = installed_status
        self.size: Optional[float] = size

        self.extra_data: Dict[str, str] = {}
        for k, v in kwargs.items():
            self.extra_data[k] = v

    def set_installed_status(self, installed_status: InstalledStatus):
        self.installed_status = installed_status
