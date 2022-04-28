from typing import Optional, Dict

class AppListElement():
    def __init__(self, name: str, description: str, app_id: str, provider: str, **kwargs):
        self.name: str = name
        self.description: str = description
        self.id = app_id
        self.provider: str = provider

        self.extra_data: Dict[str, str] = {}
        for k, v in kwargs.items():
            self.extra_data[k] = v

