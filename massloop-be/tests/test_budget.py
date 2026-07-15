"""Tests for the infrastructure-layer budget guardrails.

These cover the cost/budget SLO that docs/roast_infrastructure.md (C1)
flags as dead config. The guardrail lives in app.services.externals and is
now imported by the live app via app.main.budget_guardrails.
"""

import pytest

from app.services.externals import (
    SunoGuardrails,
    build_guardrails,
    BudgetExceededError,
)
from app.config import settings


def test_budget_status_starts_zero():
    g = SunoGuardrails(daily_limit_eur=10.0, max_track_cost_eur=3.0)
    status = g.get_budget_status()
    assert status.daily_spend_eur == 0.0
    assert status.daily_limit_eur == 10.0
    assert status.remaining_eur == 10.0
    assert status.utilization_pct == 0.0


def test_record_generation_accumulates_spend():
    g = SunoGuardrails(daily_limit_eur=10.0, max_track_cost_eur=3.0,
                       cost_per_token_eur=0.05)
    # 20 tokens * 0.05 EUR = 1.0 EUR
    cost = g.record_generation(20)
    assert cost == pytest.approx(1.0)
    assert g.get_budget_status().daily_spend_eur == pytest.approx(1.0)
    assert g.get_budget_status().remaining_eur == pytest.approx(9.0)


def test_can_afford_respects_remaining_budget():
    g = SunoGuardrails(daily_limit_eur=1.0, max_track_cost_eur=3.0,
                       cost_per_token_eur=0.05)
    # 10 tokens -> 0.5 EUR, within the 1.0 EUR daily limit
    assert g.can_afford(10) is True
    # 100 tokens -> 5.0 EUR, exceeds the 1.0 EUR daily limit
    assert g.can_afford(100) is False


def test_check_budget_raises_when_per_track_ceiling_exceeded():
    g = SunoGuardrails(daily_limit_eur=100.0, max_track_cost_eur=1.0,
                       cost_per_token_eur=0.05)
    # 100 tokens -> 5.0 EUR > 1.0 EUR per-track ceiling
    with pytest.raises(BudgetExceededError):
        g.check_budget(100)


def test_check_budget_raises_when_daily_limit_exceeded():
    g = SunoGuardrails(daily_limit_eur=1.0, max_track_cost_eur=10.0,
                       cost_per_token_eur=0.05)
    # 100 tokens -> 5.0 EUR > 1.0 EUR daily limit
    with pytest.raises(BudgetExceededError):
        g.check_budget(100)


def test_check_budget_passes_within_limits():
    g = SunoGuardrails(daily_limit_eur=10.0, max_track_cost_eur=3.0,
                       cost_per_token_eur=0.05)
    # 40 tokens -> 2.0 EUR, within both daily limit and per-track ceiling
    g.check_budget(40)  # should not raise


def test_build_guardrails_uses_config_defaults():
    g = build_guardrails(
        daily_limit_eur=settings.daily_budget_eur,
        max_track_cost_eur=settings.max_track_cost_eur,
    )
    assert g.daily_limit_eur == settings.daily_budget_eur
    assert g.max_track_cost_eur == settings.max_track_cost_eur


def test_live_app_guardrail_is_wired():
    import app.main  # noqa: F401  (import side-effects build the guardrail)
    assert isinstance(app.main.budget_guardrails, SunoGuardrails)
    assert app.main.budget_guardrails.daily_limit_eur == settings.daily_budget_eur
