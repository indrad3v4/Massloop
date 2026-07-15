"""Massloop.ai - External Adapters (Infrastructure Layer).

Layer 4: Implements interfaces with external services.

This module provides the budget/cost guardrails that the documented
architecture (docs/roast_infrastructure.md, C1) requires on the live
generation path. The budget configuration in app.config (daily_budget_eur,
max_track_cost_eur) is enforced here and is importable from the running app.

No heavy third-party audio deps (librosa/numpy/pygame) are imported at
module top-level so this module can be imported in CI and in minimal
environments.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time


class BudgetExceededError(Exception):
    """Raised when a generation would exceed the configured budget.

    Referenced by app.services.interfaces.AIGenerationPort.generate_track
    but previously never defined (dead-code rot). Now defined here so the
    budget guardrail contract is real.
    """

    def __init__(self, message: str, *, remaining_eur: float = 0.0,
                 requested_eur: float = 0.0) -> None:
        super().__init__(message)
        self.remaining_eur = remaining_eur
        self.requested_eur = requested_eur


@dataclass
class BudgetStatus:
    """Snapshot of the current budget position."""
    daily_spend_eur: float
    daily_limit_eur: float
    remaining_eur: float
    utilization_pct: float
    last_reset_day: str

    def to_dict(self) -> Dict[str, float]:
        return {
            "daily_spend_eur": self.daily_spend_eur,
            "daily_limit_eur": self.daily_limit_eur,
            "remaining_eur": self.remaining_eur,
            "utilization_pct": self.utilization_pct,
        }


class SunoGuardrails:
    """Budget and cost guardrails with configurable limits.

    Daily budget is enforced against a rolling calendar-day window using
    time.strftime("%Y-%m-%d") as the day key, so a fresh day resets spend.

    Cost model: generation cost is estimated from token usage. The original
    implementation used a flat 0.05 EUR/token heuristic; here we keep the
    per-call estimate injectable so it can be tuned per provider without
    changing the guardrail logic.
    """

    def __init__(
        self,
        daily_limit_eur: float = 10.0,
        max_track_cost_eur: float = 3.0,
        cost_per_token_eur: float = 0.05,
    ) -> None:
        self.daily_limit_eur = float(daily_limit_eur)
        self.max_track_cost_eur = float(max_track_cost_eur)
        self.cost_per_token_eur = float(cost_per_token_eur)
        self.daily_spend = 0.0
        self.generation_history: List[Dict[str, Any]] = []
        self._day_key = self._current_day_key()

    @staticmethod
    def _current_day_key() -> str:
        return time.strftime("%Y-%m-%d")

    def _roll_day_if_needed(self) -> None:
        today = self._current_day_key()
        if today != self._day_key:
            # New calendar day -> reset daily spend.
            self._day_key = today
            self.daily_spend = 0.0

    @property
    def remaining_eur(self) -> float:
        return max(0.0, self.daily_limit_eur - self.daily_spend)

    def get_budget_status(self) -> BudgetStatus:
        """Return the current budget position."""
        self._roll_day_if_needed()
        limit = self.daily_limit_eur
        utilization = (self.daily_spend / limit) * 100 if limit > 0 else 0.0
        return BudgetStatus(
            daily_spend_eur=self.daily_spend,
            daily_limit_eur=limit,
            remaining_eur=self.remaining_eur,
            utilization_pct=utilization,
            last_reset_day=self._day_key,
        )

    def estimate_cost(self, tokens_used: int) -> float:
        """Estimate EUR cost for a given token count."""
        return max(0.0, float(tokens_used)) * self.cost_per_token_eur

    def can_afford(self, tokens_used: int) -> bool:
        """True if a generation of `tokens_used` would fit in remaining budget
        AND under the per-track cost ceiling."""
        self._roll_day_if_needed()
        cost = self.estimate_cost(tokens_used)
        return cost <= self.remaining_eur and cost <= self.max_track_cost_eur

    def check_budget(self, tokens_used: int) -> None:
        """Raise BudgetExceededError if a generation of `tokens_used` is not
        allowed. Call this BEFORE spending on a generation."""
        self._roll_day_if_needed()
        cost = self.estimate_cost(tokens_used)
        if cost > self.max_track_cost_eur:
            raise BudgetExceededError(
                f"Estimated track cost {cost:.4f} EUR exceeds per-track "
                f"ceiling {self.max_track_cost_eur:.4f} EUR.",
                remaining_eur=self.remaining_eur,
                requested_eur=cost,
            )
        if cost > self.remaining_eur:
            raise BudgetExceededError(
                f"Estimated track cost {cost:.4f} EUR exceeds remaining "
                f"daily budget {self.remaining_eur:.4f} EUR "
                f"(limit {self.daily_limit_eur:.4f} EUR).",
                remaining_eur=self.remaining_eur,
                requested_eur=cost,
            )

    def record_generation(self, tokens_used: int) -> float:
        """Record a generation's token usage and return its estimated cost.

        Mirrors the original SunoGuardrails.record_generation semantics.
        """
        self._roll_day_if_needed()
        cost = self.estimate_cost(tokens_used)
        self.daily_spend += cost
        self.generation_history.append(
            {
                "timestamp": time.time(),
                "tokens": tokens_used,
                "cost_eur": cost,
            }
        )
        return cost


def build_guardrails(
    daily_limit_eur: float = 10.0,
    max_track_cost_eur: float = 3.0,
    cost_per_token_eur: float = 0.05,
) -> SunoGuardrails:
    """Factory used by the live app to construct guardrails from config."""
    return SunoGuardrails(
        daily_limit_eur=daily_limit_eur,
        max_track_cost_eur=max_track_cost_eur,
        cost_per_token_eur=cost_per_token_eur,
    )
