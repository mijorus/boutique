from typing import Dict
from ..models.Provider import Provider
from .FlatpakProvider import FlatpakProvider
from .AppImageProvider import AppImageProvider

# A list containing all the "Providers" currently only Flatpak is supported
# but I might need to add other ones in the future
providers: Dict[str, Provider] = { 
    'flatpak': FlatpakProvider(),
    'appimage': AppImageProvider()
}