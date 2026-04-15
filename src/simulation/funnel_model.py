"""
AARRR Funnel Model — Pirate Metrics Funnel Simulation
=====================================================
Models the full Acquisition → Activation → Retention → Revenue → Referral
funnel with configurable stage-level conversion rates and drop-off modeling.

Author: Brian Stratton
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class FunnelStageConfig:
      """Configuration for a single funnel stage."""
      name: str
      conversion_rate: float
      cost_per_unit: float = 0.0
      revenue_per_unit: float = 0.0


class AARRRFunnel:
      """
          AARRR (Pirate Metrics) funnel simulator.

              Models user flow through Acquisition → Activation → Retention →
                  Revenue → Referral stages with conversion rates at each step.

                      Usage:
                              funnel = AARRRFunnel(top_of_funnel=10000)
                                      results = funnel.simulate()
                                              funnel.print_funnel(results)
                                                  """

    def __init__(self, top_of_funnel: int = 10000,
                                  acquisition_rate: float = 0.08,
                                  activation_rate: float = 0.60,
                                  retention_rate_m1: float = 0.40,
                                  retention_rate_m3: float = 0.25,
                                  retention_rate_m6: float = 0.15,
                                  revenue_conversion: float = 0.04,
                                  referral_rate: float = 0.15,
                                  cac: float = 50.0,
                                  arpu: float = 29.99):
                                            self.top_of_funnel = top_of_funnel
                                            self.stages = [
                                                FunnelStageConfig("Visitors", 1.0),
                                                FunnelStageConfig("Acquisition", acquisition_rate, cost_per_unit=cac),
                                                FunnelStageConfig("Activation", activation_rate),
                                                FunnelStageConfig("Retention (M1)", retention_rate_m1),
                                                FunnelStageConfig("Retention (M3)", retention_rate_m3),
                                                FunnelStageConfig("Retention (M6)", retention_rate_m6),
                                                FunnelStageConfig("Revenue", revenue_conversion, revenue_per_unit=arpu),
                                                FunnelStageConfig("Referral", referral_rate),
                                            ]

    def simulate(self) -> pd.DataFrame:
              """
                      Run funnel simulation and return stage-by-stage metrics.

                              Returns:
                                          DataFrame with columns: stage, users, conversion_rate,
                                                      drop_off, cumulative_conversion, cost, revenue
                                                              """
              results = []
              current_users = self.top_of_funnel

        for i, stage in enumerate(self.stages):
                      if i == 0:
                                        users_at_stage = current_users
else:
                  users_at_stage = int(current_users * stage.conversion_rate)

            drop_off = current_users - users_at_stage if i > 0 else 0
            cumulative = users_at_stage / self.top_of_funnel
            cost = users_at_stage * stage.cost_per_unit
            revenue = users_at_stage * stage.revenue_per_unit

            results.append({
                              "stage": stage.name,
                              "users": users_at_stage,
                              "conversion_rate": stage.conversion_rate if i > 0 else 1.0,
                              "drop_off": drop_off,
                              "cumulative_conversion": cumulative,
                              "cost": cost,
                              "revenue": revenue,
            })
            current_users = users_at_stage

        return pd.DataFrame(results)

    def print_funnel(self, df: pd.DataFrame) -> None:
              """Print formatted funnel visualization to console."""
              print("\n" + "=" * 65)
              print("  AARRR FUNNEL ANALYSIS")
              print("=" * 65)
              max_width = 40

        for _, row in df.iterrows():
                      bar_width = int(row["cumulative_conversion"] * max_width)
                      bar = "█" * bar_width + "░" * (max_width - bar_width)
                      pct = row["cumulative_conversion"] * 100
                      print(f"  {row['stage']:<20} {bar} {row['users']:>8,} ({pct:.1f}%)")

        print("-" * 65)
        total_cost = df["cost"].sum()
        total_revenue = df["revenue"].sum()
        print(f"  Total Acquisition Cost:  ${total_cost:,.0f}")
        print(f"  Total Revenue:           ${total_revenue:,.0f}")
        print(f"  ROI:                     {(total_revenue/total_cost - 1)*100:.1f}%" if total_cost > 0 else "  ROI: N/A")
        print("=" * 65 + "\n")

    def calculate_ltv(self, arpu: float = 29.99,
                                            monthly_churn: float = 0.05,
                                            months: int = 36) -> Dict:
                                                      """
                                                              Calculate Customer Lifetime Value using retention-based model.

                                                                      Args:
                                                                                  arpu: Average Revenue Per User per month
                                                                                              monthly_churn: Monthly churn rate
                                                                                                          months: Projection horizon
                                                                                                          
                                                                                                                  Returns:
                                                                                                                              Dictionary with LTV metrics
                                                                                                                                      """
                                                      retention_curve = [(1 - monthly_churn) ** m for m in range(months)]
                                                      cumulative_revenue = [arpu * r for r in retention_curve]
                                                      ltv = sum(cumulative_revenue)

        avg_lifetime_months = sum(retention_curve)

        return {
                      "ltv": ltv,
                      "avg_lifetime_months": avg_lifetime_months,
                      "retention_curve": retention_curve,
                      "monthly_revenue_curve": cumulative_revenue,
                      "ltv_to_cac_ratio": ltv / self.stages[1].cost_per_unit
                          if self.stages[1].cost_per_unit > 0 else float("inf"),
        }


if __name__ == "__main__":
      funnel = AARRRFunnel(top_of_funnel=50000)
      results = funnel.simulate()
      funnel.print_funnel(results)

    ltv_metrics = funnel.calculate_ltv()
    print(f"  Customer LTV: ${ltv_metrics['ltv']:,.2f}")
    print(f"  Avg Lifetime: {ltv_metrics['avg_lifetime_months']:.1f} months")
    print(f"  LTV:CAC Ratio: {ltv_metrics['ltv_to_cac_ratio']:.1f}x")
