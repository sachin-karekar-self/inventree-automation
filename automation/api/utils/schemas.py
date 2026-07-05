"""Lightweight response-schema assertions for InvenTree Part API resources.

Deliberately dependency-free: asserts presence and Python type of required keys.
Types derived from the published OpenAPI schema (Part serializer) — IPN maxLength 100,
read-only computed fields, etc.
"""
from __future__ import annotations

from typing import Any

# key -> tuple of acceptable Python types (None allowed where schema is nullable)
PART_SCHEMA: dict[str, tuple[type, ...]] = {
    "pk": (int,),
    "name": (str,),
    "description": (str,),
    "category": (int, type(None)),
    "IPN": (str, type(None)),
    "active": (bool,),
    "assembly": (bool,),
    "component": (bool,),
    "virtual": (bool,),
    "trackable": (bool,),
    "purchaseable": (bool,),
    "salable": (bool,),
    "units": (str, type(None)),
}

CATEGORY_SCHEMA: dict[str, tuple[type, ...]] = {
    "pk": (int,),
    "name": (str,),
    "parent": (int, type(None)),
}

PAGINATED_KEYS = ("count", "next", "previous", "results")


def assert_schema(body: dict[str, Any], schema: dict[str, tuple[type, ...]], where: str = "") -> None:
    """Assert every schema key exists in body with an acceptable type."""
    missing = [k for k in schema if k not in body]
    assert not missing, f"{where}: missing keys {missing}; got keys {sorted(body)}"
    for key, types in schema.items():
        assert isinstance(body[key], types), (
            f"{where}: key '{key}' expected {types}, got {type(body[key])} = {body[key]!r}"
        )


def assert_paginated(body: dict[str, Any], where: str = "") -> list[dict[str, Any]]:
    """Assert DRF pagination envelope; return results list."""
    for key in PAGINATED_KEYS:
        assert key in body, f"{where}: paginated envelope missing '{key}'"
    assert isinstance(body["count"], int)
    assert isinstance(body["results"], list)
    return body["results"]
