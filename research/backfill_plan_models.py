from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class BackfillPlanItem:
    priority_rank: int
    event_category: str
    primary_ticker: str | None
    related_ticker: str | None
    relationship_type: str | None
    target_type: str
    current_sample_size: int
    desired_min_sample_size: int
    gap_size: int
    why_it_matters: str
    suggested_source_type: str
    suggested_historical_examples_needed: list[str]
    planner_score: float
    source_gap_key: str
    notes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BackfillPlanGroup:
    group_key: str
    source_type: str
    event_category: str
    plan_item_keys: list[str]
    total_gap_size: int
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TargetedBackfillPlan:
    generated_from_report: str
    plan_items: tuple[BackfillPlanItem, ...]
    groups: tuple[BackfillPlanGroup, ...]
    notes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_from_report": self.generated_from_report,
            "plan_items": [item.to_dict() for item in self.plan_items],
            "groups": [group.to_dict() for group in self.groups],
            "notes": self.notes,
        }
