import pytest
from pydantic import ValidationError

from triage.schema import TriageDecision


def test_valid_decision_is_accepted() -> None:
    decision = TriageDecision(
        category="billing",
        priority="P2",
        route="billing-team",
        rationale="The customer reports a duplicate charge.",
    )

    assert decision.model_dump(mode="json") == {
        "category": "billing",
        "priority": "P2",
        "route": "billing-team",
        "rationale": "The customer reports a duplicate charge.",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("category", "other"),
        ("priority", "P5"),
        ("route", "support-team"),
    ],
)
def test_unsupported_values_are_rejected(field: str, value: str) -> None:
    payload = {
        "category": "billing",
        "priority": "P2",
        "route": "billing-team",
        "rationale": "The customer reports a duplicate charge.",
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        TriageDecision.model_validate(payload)


@pytest.mark.parametrize(
    ("category", "route"),
    [
        ("billing", "billing-team"),
        ("bug", "bug-team"),
        ("access", "access-team"),
        ("performance", "performance-team"),
        ("how-to", "how-to-team"),
    ],
)
def test_each_category_maps_to_its_route(category: str, route: str) -> None:
    decision = TriageDecision(
        category=category,
        priority="P3",
        route=route,
        rationale="The ticket needs the matching specialist team.",
    )

    assert decision.route.value == route


@pytest.mark.parametrize(
    ("category", "route", "expected_route"),
    [
        ("billing", "bug-team", "billing-team"),
        ("bug", "billing-team", "bug-team"),
        ("access", "billing-team", "access-team"),
        ("performance", "billing-team", "performance-team"),
        ("how-to", "billing-team", "how-to-team"),
    ],
)
def test_route_must_match_category(
    category: str, route: str, expected_route: str
) -> None:
    with pytest.raises(ValidationError, match=f"route must be '{expected_route}'"):
        TriageDecision(
            category=category,
            priority="P3",
            route=route,
            rationale="The export button fails in Firefox.",
        )


@pytest.mark.parametrize(
    "rationale",
    [
        "",
        "First sentence. Second sentence.",
        "First sentence. second sentence.",
        'First sentence." Next sentence.',
        "First!Second.",
        "!!!",
        "The customer reports a duplicate charge",
    ],
)
def test_rationale_must_be_one_sentence(rationale: str) -> None:
    with pytest.raises(ValidationError, match="rationale must be one sentence"):
        TriageDecision(
            category="how-to",
            priority="P4",
            route="how-to-team",
            rationale=rationale,
        )


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="extra"):
        TriageDecision(
            category="access",
            priority="P1",
            route="access-team",
            rationale="The whole team is locked out.",
            source="customer",
        )


def test_json_object_is_validated() -> None:
    decision = TriageDecision.model_validate_json(
        '{"category":"performance","priority":"P3","route":"performance-team","rationale":"The dashboard loads slowly."}'
    )

    assert decision.category.value == "performance"


def test_abbreviation_does_not_create_a_second_sentence() -> None:
    decision = TriageDecision(
        category="how-to",
        priority="P4",
        route="how-to-team",
        rationale="Use e.g. this workflow.",
    )

    assert decision.rationale == "Use e.g. this workflow."
