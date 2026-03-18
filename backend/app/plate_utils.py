import re

TURKISH_PLATE_RE = re.compile(r"^(\d{2})([A-Z]{1,3})(\d{2,4})$")

def normalize_plate(plate: str) -> str:
    return plate.replace(" ", "").upper()

def is_valid_turkish_plate(normalized: str) -> bool:
    return bool(TURKISH_PLATE_RE.match(normalized))

def format_plate_display(normalized: str) -> str:
    match = TURKISH_PLATE_RE.match(normalized)
    if not match:
        return normalized
    city, letters, digits = match.groups()
    return f"{city} {letters} {digits}"
