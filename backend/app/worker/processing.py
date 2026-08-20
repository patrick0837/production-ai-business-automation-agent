def determine_priority(content: str) -> str:
    return (
        "high"
        if "enterprise" in content.lower()
        else "normal"
    )