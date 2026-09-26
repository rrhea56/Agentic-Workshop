"""Validation models for triage decisions."""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class Category(StrEnum):
    BILLING = "billing"
    BUG = "bug"
    ACCESS = "access"
    PERFORMANCE = "performance"
    HOW_TO = "how-to"


class Priority(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class Route(StrEnum):
    BILLING_TEAM = "billing-team"
    BUG_TEAM = "bug-team"
    ACCESS_TEAM = "access-team"
    PERFORMANCE_TEAM = "performance-team"
    HOW_TO_TEAM = "how-to-team"


_ROUTE_BY_CATEGORY = {
    Category.BILLING: Route.BILLING_TEAM,
    Category.BUG: Route.BUG_TEAM,
    Category.ACCESS: Route.ACCESS_TEAM,
    Category.PERFORMANCE: Route.PERFORMANCE_TEAM,
    Category.HOW_TO: Route.HOW_TO_TEAM,
}
_SENTENCE_BOUNDARY = re.compile(r"[.!?](?=\s+[A-Z0-9])")


class TriageDecision(BaseModel):
    """A complete, policy-routable triage decision."""

    model_config = ConfigDict(extra="forbid")

    category: Category
    priority: Priority
    route: Route
    rationale: str

    @field_validator("rationale")
    @classmethod
    def rationale_is_one_sentence(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("rationale must be one sentence")
        if "\n" in value or not value.endswith((".", "!", "?")):
            raise ValueError("rationale must be one sentence")
        if _SENTENCE_BOUNDARY.search(value):
            raise ValueError("rationale must be one sentence")
        return value

    @model_validator(mode="after")
    def route_matches_category(self) -> "TriageDecision":
        expected_route = _ROUTE_BY_CATEGORY[self.category]
        if self.route != expected_route:
            raise ValueError(
                f"route must be {expected_route.value!r} for category {self.category.value!r}"
            )
        return self
