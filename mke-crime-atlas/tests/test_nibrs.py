from mke_crime import nibrs


def test_split_codes_handles_blanks_and_case():
    assert nibrs.split_codes("13b; 13C;") == ["13B", "13C"]
    assert nibrs.split_codes("") == []
    assert nibrs.split_codes(None) == []


def test_category_for_code():
    assert nibrs.category_for_code("13A") == "Violent"
    assert nibrs.category_for_code("520") == "Weapons"
    assert nibrs.category_for_code("240") == "Property"
    assert nibrs.category_for_code("35A") == "Drugs"
    assert nibrs.category_for_code("90Z") == "Other"


def test_incident_takes_most_serious_group():
    assert nibrs.categorize_incident(["290", "13B"]) == "Violent"
    assert nibrs.categorize_incident(["35A", "520"]) == "Weapons"
    assert nibrs.categorize_incident([]) == "Other"
