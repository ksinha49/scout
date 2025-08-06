import re


def slugify(value: str) -> str:
    """Simplify a string into a slug usable in collection names."""
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def build_user_collection_name(user_id: str | int) -> str:
    """Return sanitized collection name for a user."""
    return f"user-{user_id}"


def build_kb_collection_name(kb_name: str, kb_id: str | int) -> str:
    """Return sanitized collection name for a knowledge base."""
    slug = slugify(kb_name)
    return f"kb-{slug}-{kb_id}"
