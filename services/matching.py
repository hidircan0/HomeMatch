from datetime import date

from models import PostType, RoommatePost

WEIGHTS = {"location": 30, "rent": 30, "lifestyle": 25, "move_date": 15}


def _compatible_lifestyle(seeker: RoommatePost, offer: RoommatePost) -> int:
    seeker_data = seeker.seeker_lifestyle or {}
    rules = offer.household_rules or {}
    checks: list[int] = []
    if "smokes" in seeker_data and "smoking_allowed" in rules:
        checks.append(100 if not seeker_data["smokes"] or rules["smoking_allowed"] else 0)
    if "has_pets" in seeker_data and "pets_allowed" in rules:
        checks.append(100 if not seeker_data["has_pets"] or rules["pets_allowed"] else 0)
    for field in ("sleep_schedule", "cleanliness", "guest_frequency"):
        if field in seeker_data and field in rules:
            seeker_value, rule_value = seeker_data[field], rules[field]
            checks.append(100 if "flexible" in (seeker_value, rule_value) or seeker_value == rule_value else 0)
    return round(sum(checks) / len(checks)) if checks else 0


def score_pair(first: RoommatePost, second: RoommatePost) -> tuple[int, dict[str, int]]:
    if first.post_type == PostType.LOOKING_FOR_ROOM:
        seeker, offer = first, second
    else:
        seeker, offer = second, first

    location = 100 if seeker.district.casefold() == offer.district.casefold() else (
        50 if seeker.city.casefold() == offer.city.casefold() else 0
    )
    budget, share = float(seeker.monthly_budget or 0), float(offer.monthly_share or 0)
    rent = max(0, round((1 - share / budget) * 100)) if budget > 0 else 0
    lifestyle = _compatible_lifestyle(seeker, offer)
    day_difference = (offer.available_from - seeker.available_from).days
    move_date = 100 if day_difference <= 0 else max(0, 100 - round(day_difference * 100 / 30))

    breakdown = {"location": location, "rent": rent, "lifestyle": lifestyle, "move_date": move_date}
    score = round(sum(breakdown[key] * weight for key, weight in WEIGHTS.items()) / sum(WEIGHTS.values()))
    return score, breakdown


def complementary(post_type: PostType) -> PostType:
    return (
        PostType.LOOKING_FOR_ROOMMATE
        if post_type == PostType.LOOKING_FOR_ROOM
        else PostType.LOOKING_FOR_ROOM
    )
