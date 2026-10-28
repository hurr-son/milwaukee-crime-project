"""FBI NIBRS offense codes and the offense groups used throughout the app."""
import re

# Most serious first. An incident with several offenses takes the earliest group in this list.
CATEGORIES = ["Violent", "Weapons", "Property", "Drugs", "Other"]

_PATTERNS = [
    ("Violent", re.compile(r"^(09A|09B|100|11[A-D]|120|13[ABC]|36[AB])$")),
    ("Weapons", re.compile(r"^520$")),
    ("Property", re.compile(r"^(200|210|220|23[A-H]|240|250|26[A-H]|270|280|290)$")),
    ("Drugs", re.compile(r"^35[AB]$")),
]

OFFENSE_NAMES = {
    "09A": "Murder & nonnegligent manslaughter", "09B": "Negligent manslaughter", "100": "Kidnapping / abduction",
    "11A": "Rape", "11B": "Sodomy", "11C": "Sexual assault with an object", "11D": "Fondling",
    "120": "Robbery", "13A": "Aggravated assault", "13B": "Simple assault", "13C": "Intimidation",
    "200": "Arson", "210": "Extortion / blackmail", "220": "Burglary",
    "23A": "Pocket-picking", "23B": "Purse-snatching", "23C": "Shoplifting", "23D": "Theft from building",
    "23E": "Theft from coin machine", "23F": "Theft from motor vehicle", "23G": "Theft of vehicle parts",
    "23H": "All other larceny", "240": "Motor vehicle theft", "250": "Counterfeiting / forgery",
    "26A": "False pretenses / swindle", "26B": "Credit card / ATM fraud", "26C": "Impersonation",
    "26D": "Welfare fraud", "26E": "Wire fraud", "26F": "Identity theft", "26G": "Hacking / computer invasion",
    "270": "Embezzlement", "280": "Stolen property offenses", "290": "Vandalism / property damage",
    "35A": "Drug / narcotic violations", "35B": "Drug equipment violations",
    "36A": "Incest", "36B": "Statutory rape", "370": "Pornography / obscene material",
    "40A": "Prostitution", "520": "Weapon law violations", "64A": "Human trafficking, sex acts",
    "720": "Animal cruelty", "90A": "Bad checks", "90B": "Curfew / loitering", "90C": "Disorderly conduct",
    "90D": "Driving under the influence", "90E": "Drunkenness", "90F": "Family offenses, nonviolent",
    "90G": "Liquor law violations", "90J": "Trespass", "90Z": "All other offenses",
    "999": "Local code 999 (unclassified)",
}


def split_codes(offense_all: str | None) -> list[str]:
    """'13B;13C' -> ['13B', '13C']. Blank or missing -> []."""
    if not isinstance(offense_all, str):
        return []
    return [c.strip().upper() for c in offense_all.split(";") if c.strip()]


def category_for_code(code: str) -> str:
    for name, pattern in _PATTERNS:
        if pattern.match(code):
            return name
    return "Other"


def categorize_incident(codes: list[str]) -> str:
    """Most serious group among an incident's offense codes."""
    if not codes:
        return "Other"
    return min((category_for_code(c) for c in codes), key=CATEGORIES.index)


def offense_name(code: str) -> str:
    return OFFENSE_NAMES.get(code, f"Code {code}")
