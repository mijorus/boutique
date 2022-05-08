
from typing import Optional

class FlatpakHistoryElement():
    def __init__(self, commit: str='', subject: str='', date: str=''):
        self.commit = commit
        self.subject = subject
        self.date = date

class AppUpdateElement():
    def __init__(self, app_id: str, size: Optional[str], **kwargs):
        self.id: str = app_id
        self.size: Optional[str] = size
        self.extra_data: dict = {}

        for k, v in kwargs.items():
            self.extra_data[k] = v
