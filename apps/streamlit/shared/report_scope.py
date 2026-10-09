"""Normalized authorization scope for every report query and cache key."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportScope:
    email: str
    can_view_all_stores: bool
    allowed_store_ids: tuple[int, ...]
    scope_id: str

    @property
    def is_allowed(self) -> bool:
        return self.can_view_all_stores or bool(self.allowed_store_ids)
