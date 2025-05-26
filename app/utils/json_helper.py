def flatten_json(y, prefix=""):
    """
    Flatten a nested JSON object into a single-level dictionary with dot notation keys.
    Args:
        y (dict or list): The JSON object to flatten.
        prefix (str): The prefix for the keys in the flattened dictionary.
    Returns:
        dict: A flattened dictionary with keys in dot notation.
    """
    out = {}
    if isinstance(y, dict):
        for k, v in y.items():
            out.update(flatten_json(v, prefix + k + "."))
    elif isinstance(y, list):
        for i, v in enumerate(y):
            out.update(flatten_json(v, prefix + str(i) + "."))
    else:
        out[prefix[:-1]] = y
    return out


def json_to_text_snippet(obj):
    """
    Convert a JSON object to a text snippet for display.
    Args:
        obj (dict): The JSON object to convert.
    Returns:
        str: A text snippet representation of the JSON object.
    """
    parts = []
    for k, v in obj.items():
        parts.append(f"{k.capitalize()}: {v}")
    return ", ".join(parts)


def validate_json(json_data):
    """
    Validate the structure of a player JSON object.
    Args:
        player_json (dict): The JSON object representing a player.
    Returns:
        bool: True if the JSON object is valid, raises an error otherwise.
    """
    required_fields = {
        "customer_id": int,
        "name": str,
        "age": int,
        "membership": str,
        "purchases_last_6_months": int,
        "total_spent": (int, float),
        "preferred_category": str,
        "last_purchase_date": str,
        "nearest_store": str,
    }

    for field, expected_type in required_fields.items():
        if field not in json_data:
            raise ValueError(f"Missing required field: {field}")
        if not isinstance(json_data[field], expected_type):
            raise TypeError(
                f"Field {field} must be of type {expected_type}, got {type(json_data[field])}"
            )

    return True
