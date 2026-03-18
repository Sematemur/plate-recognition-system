from app.plate_utils import normalize_plate, format_plate_display, is_valid_turkish_plate

def test_normalize_plate_strips_spaces():
    assert normalize_plate("34 ABC 123") == "34ABC123"

def test_normalize_plate_uppercase():
    assert normalize_plate("34 abc 123") == "34ABC123"

def test_normalize_plate_already_normalized():
    assert normalize_plate("34ABC123") == "34ABC123"

def test_is_valid_turkish_plate_3letter_3digit():
    assert is_valid_turkish_plate("34ABC123") is True

def test_is_valid_turkish_plate_3letter_2digit():
    assert is_valid_turkish_plate("34ABC12") is True

def test_is_valid_turkish_plate_2letter_3digit():
    assert is_valid_turkish_plate("06AB456") is True

def test_is_valid_turkish_plate_1letter_4digit():
    assert is_valid_turkish_plate("34A1234") is True

def test_is_valid_turkish_plate_invalid():
    assert is_valid_turkish_plate("XYZGARBAGE") is False

def test_is_valid_turkish_plate_too_short():
    assert is_valid_turkish_plate("34") is False

def test_format_plate_display_3letter_3digit():
    assert format_plate_display("34ABC123") == "34 ABC 123"

def test_format_plate_display_2letter_3digit():
    assert format_plate_display("06AB456") == "06 AB 456"

def test_format_plate_display_1letter_4digit():
    assert format_plate_display("34A1234") == "34 A 1234"
