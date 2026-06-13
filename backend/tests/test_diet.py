from backend.services.diet import diet_allows


def test_vegetarian_excludes_meat_fish_egg():
    for name in ("Chicken Biryani", "Mutton Curry", "Fish Fry", "Egg Bhurji", "Prawn Masala", "Murgh Makhani"):
        assert diet_allows("vegetarian", name, []) is False
    for name in ("Paneer Tikka", "Veg Hakka Noodles", "Aloo Gobi", "Dal Makhani", "Eggplant Parmigiana"):
        assert diet_allows("vegetarian", name, []) is True


def test_ocr_flag_respected_and_keyword_overrides():
    assert diet_allows("vegetarian", "Mystery Dish", ["non_veg"]) is False
    # A wrong "veg" flag on an obviously non-veg item still excludes (keyword wins).
    assert diet_allows("vegetarian", "Chicken Korma", ["veg"]) is False


def test_vegan_excludes_dairy_and_egg():
    assert diet_allows("vegan", "Paneer Butter Masala", ["veg"]) is False
    assert diet_allows("vegan", "Aloo Jeera", []) is True


def test_diet_variants():
    assert diet_allows("eggetarian", "Egg Curry", []) is True
    assert diet_allows("eggetarian", "Chicken 65", []) is False
    assert diet_allows("pescatarian", "Grilled Fish", []) is True
    assert diet_allows("pescatarian", "Lamb Chops", []) is False
    assert diet_allows("non-vegetarian", "Beef Steak", []) is True
