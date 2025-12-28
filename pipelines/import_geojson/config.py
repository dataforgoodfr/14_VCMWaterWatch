"""Configuration for geographic level mappings."""
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class LevelConfig:
    """Configuration for a geographic level."""
    file_suffix: str  # Pluralized version of the level (e.g., "Countries", "Regions")
    parent_level: Optional[str]  # Parent level name (e.g., "Country" for Region)
    title_property: str  # Property name in GeoJSON to map to "Title"
    code_property: str  # Property name in GeoJSON to map to "Code"


# Configuration map for each level
LEVEL_CONFIGS: Dict[str, LevelConfig] = {
    "Country": LevelConfig(
        file_suffix="countries",
        parent_level=None,
        title_property="name",
        code_property="ISO3166-1-Alpha-2",
    ),
    "Region": LevelConfig(
        file_suffix="regions",
        parent_level="Country",
        title_property="name",
        code_property="region_code",
    ),
    "Township": LevelConfig(
        file_suffix="townships",
        parent_level="Region",
        title_property="",
        code_property="",
    ),
}

EUROPEAN_COUNTRIES = {
    "AL": "Albania",
    "AD": "Andorra",
    "AT": "Austria",
    "BY": "Belarus",
    "BE": "Belgium",
    "BA": "Bosnia and Herzegovina",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "CY": "Cyprus",
    "CZ": "Czech Republic",
    "DK": "Denmark",
    "EE": "Estonia",
    "FI": "Finland",
    "FR": "France",
    "DE": "Germany",
    "GR": "Greece",
    "HU": "Hungary",
    "IS": "Iceland",
    "IE": "Ireland",
    "IT": "Italy",
    "LV": "Latvia",
    "LI": "Liechtenstein",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MT": "Malta",
    "MD": "Moldova",
    "MC": "Monaco",
    "ME": "Montenegro",
    "NL": "Netherlands",
    "MK": "North Macedonia",
    "NO": "Norway",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "RU": "Russia",
    "SM": "San Marino",
    "RS": "Serbia",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "ES": "Spain",
    "SE": "Sweden",
    "CH": "Switzerland",
    "UA": "Ukraine",
    "GB": "United Kingdom",
    "VA": "Vatican City"
}
