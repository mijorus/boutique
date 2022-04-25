from typing import Optional

class AppListElement():
    def __init__(self, name: str, description: str, app_id: str, icon: str=None):
        self.name: str = name
        self.description: str = description
        self.id = app_id
        self.icon: Optional[str] = icon
