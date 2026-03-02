from __future__ import annotations


def humanise_token(token: str) -> str:
    if not token:
        return ""

    parts = token.replace("_", " ").split()
    title = " ".join(word.capitalize() for word in parts)

    replacements = {
        "Wifi": "Wi-Fi",
        "Wifi 6": "Wi-Fi 6",
        "Wifi 7": "Wi-Fi 7",
        "M2": "m2",
        "Kw": "kW",
        "Db": "dB",
        "Fttp": "FTTP",
        "Dsl": "DSL",
    }

    for src, dst in replacements.items():
        title = title.replace(src, dst)

    return title
