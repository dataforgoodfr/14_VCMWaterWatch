"""Configuration for geographic level mappings."""

from typing import Dict
from dataclasses import dataclass


@dataclass
class LevelConfig:
    """Configuration for a geographic level."""

    file_suffix: str  # Pluralized version of the level (e.g., "Countries", "Regions")
    parent_level: str | None  # Parent level name (e.g., "Country" for Region)
    title_property: str  # Property name in GeoJSON to map to "Title"
    code_property: str  # Property name in GeoJSON to map to "Code"
    parent_property: str | None = None  # Property name in GeoJSON to map to Parent.Code


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
    "Municipality": LevelConfig(
        file_suffix="municipalities",
        parent_level="Country",
        title_property="COMM_NAME",
        code_property="COMM_ID",
        parent_property="CNTR_CODE",
    ),
}

EUROPEAN_COUNTRIES = {
    "AT": "Austria",
    "DK": "Denmark",
    "FR": "France",
    "DE": "Germany",
    "IT": "Italy",
    "NL": "Netherlands",
    "NO": "Norway",
    "PL": "Poland",
    "PT": "Portugal",
    "ES": "Spain",
    "SE": "Sweden",
    "GB": "United Kingdom",
}
# EUROPEAN_COUNTRIES = {
#     "AL": "Albania",
#     "AD": "Andorra",
#     "AT": "Austria",
#     "BY": "Belarus",
#     "BE": "Belgium",
#     "BA": "Bosnia and Herzegovina",
#     "BG": "Bulgaria",
#     "HR": "Croatia",
#     "CY": "Cyprus",
#     "CZ": "Czech Republic",
#     "DK": "Denmark",
#     "EE": "Estonia",
#     "FI": "Finland",
#     "FR": "France",
#     "DE": "Germany",
#     "GR": "Greece",
#     "HU": "Hungary",
#     "IS": "Iceland",
#     "IE": "Ireland",
#     "IT": "Italy",
#     "LV": "Latvia",
#     "LI": "Liechtenstein",
#     "LT": "Lithuania",
#     "LU": "Luxembourg",
#     "MT": "Malta",
#     "MD": "Moldova",
#     "MC": "Monaco",
#     "ME": "Montenegro",
#     "NL": "Netherlands",
#     "MK": "North Macedonia",
#     "NO": "Norway",
#     "PL": "Poland",
#     "PT": "Portugal",
#     "RO": "Romania",
#     "RU": "Russia",
#     "SM": "San Marino",
#     "RS": "Serbia",
#     "SK": "Slovakia",
#     "SI": "Slovenia",
#     "ES": "Spain",
#     "SE": "Sweden",
#     "CH": "Switzerland",
#     "UA": "Ukraine",
#     "GB": "United Kingdom",
#     "VA": "Vatican City",
# }
