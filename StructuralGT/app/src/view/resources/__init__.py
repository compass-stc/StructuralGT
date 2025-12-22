"""Resources module for StructuralGT GUI."""

from .resources import *  # noqa: F403

# Resource prefix for QRC resources
RESOURCE_PREFIX = ":/resources"


def get_resource_path(*path_parts: str) -> str:
    """Get resource path using QRC format."""
    path = "/".join(path_parts)
    return f"{RESOURCE_PREFIX}/{path}"


def get_app_icon_path() -> str:
    """Get app icon resource path."""
    return get_resource_path("icons", "StructuralGT.png")


def get_icon_path(icon_name: str, theme: str) -> str:
    """Get icon resource path."""
    return get_resource_path("icons", theme, icon_name)


def get_style_path(style_name: str = "custom_styles.qss") -> str:
    """Get style resource path."""
    return get_resource_path("style", style_name)
