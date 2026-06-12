def calculate_points_by_weight(waste_type: str, weight_grams: float) -> int:
    """
    Calculates points based on weight.
    For example: 20 points per kg (1000g) of paper.
    Enforces a minimum of 50 grams.
    """
    if waste_type == "paper":
        if weight_grams < 50:
            return 0
        # 20 points per 1000 grams -> 1 point per 50 grams
        return int(weight_grams / 50)
    return 0

def calculate_points_by_item(waste_type: str) -> int:
    """
    Calculates points based on item count.
    For example: 2 points per plastic bottle, 5 points per paper piece.
    """
    if waste_type == "plastic":
        return 2
    if waste_type == "paper":
        return 5
    return 0
