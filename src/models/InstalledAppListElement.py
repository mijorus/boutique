from typing import Optional

class InstalledAppListElement():
    def __init__(self, name: str, description: str, icon: str=None):
        self.name: str = name
        self.description: str = description
        self.icon: Optional[str] = icon
