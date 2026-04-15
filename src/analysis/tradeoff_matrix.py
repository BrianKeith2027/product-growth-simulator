"""
Trade-Off Matrix - Strategy Comparison Engine
==============================================
Compares multiple growth strategies across cost, revenue, timeline,
and risk dimensions to generate stakeholder-ready decision matrices.

Author: Brian Stratton
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List
from copy import deepcopy
import logging

from ..simulation.growth_engine import GrowthEngine, GrowthLevers, SimulationConfig

logger = logging.getLogger(__name__)


@dataclass
class Strategy:
      """A named growth strategy with modified lever values."""
      name: str
      levers: GrowthLevers
      monthly_investment: float
      description: str = ""


class TradeOffMatrix:
      """
          Compares growth strategies across cost, revenue, timeline, and risk.
              Runs simulations for each strategy and builds a comparison matrix
                  suitable for stakeholder presentations and board discussions.
                      """

    DEFAULT_STRATEGIES = {
              "Retention-First": {
                            "monthly_churn_rate": 0.03,
                            "activation_rate": 0.70,
                            "monthly_investment": 50000,
                            "description": "Focus on reducing churn and improving activation",
              },
              "Acquisition Blitz": {
                            "monthly_new_users": 2500,
                            "cac": 65.0,
                            "monthly_investment": 162500,
                            "description": "Aggressive paid acquisition to maximize top-of-funnel",
              },
              "Balanced Growth": {
                            "monthly_new_users": 1500,
                            "monthly_churn_rate": 0.04,
                            "activation_rate": 0.65,
                            "monthly_investment": 87500,
                            "description": "Equal investment across acquisition and retention",
              },
              "Viral + Pricing": {
                            "viral_coefficient": 0.30,
                            "arpu": 39.99,
                            "referral_conversion_rate": 0.35,
                            "monthly_investment": 37500,
                            "description": "Invest in referral program and premium pricing",
              },
    }

    def __init__(self, base_levers=None, config=None):
              self.base_levers = base_levers or GrowthLevers()
              self.config = config or SimulationConfig(n_simulations=5000)
              self.strategies = []

    def add_strategy(self, name, lever_overrides, monthly_investment, description=""):
              """Add a custom strategy with specific lever overrides."""
              levers = deepcopy(self.base_levers)
              for key, value in lever_overrides.items():
                            if hasattr(levers, key):
                                              setattr(levers, key, value)
                                      self.strategies.append(Strategy(
                            name=name, levers=levers,
                            monthly_investment=monthly_investment,
                            description=description,
                            ))

          def load_default_strategies(self):
                    """Load the built-in default strategy set."""
                    for name, cfg in self.DEFAULT_STRATEGIES.items():
                                  overrides = {k: v for k, v in cfg.items()
                                                                        if k not in ("monthly_investment", "description")}
                                  self.add_strategy(
                                      name=name, lever_overrides=overrides,
                                      monthly_investment=cfg["monthly_investment"],
                                      description=cfg.get("description", ""),
                                  )

                def evaluate(self):
                          """Evaluate all strategies and return comparison DataFrame."""
                          results = []
                          n_months = self.config.n_months

        for strategy in self.strategies:
                      logger.info("Evaluating strategy: %s", strategy.name)
                      engine = GrowthEngine(levers=strategy.levers, config=self.config)
                      result = engine.run_simulation()

            total_cost = strategy.monthly_investment * n_months
            total_revenue = float(result.revenue_trajectories.mean(axis=0).sum())
            months_to_target = result.summary.get("median_months_to_target", None)
            pct_reached = result.summary["pct_reached_target"]

            if pct_reached >= 70 and total_cost < 2_000_000:
                              risk = "Low"
elif pct_reached >= 40:
                  risk = "Medium"
else:
                  risk = "High"

            roi = ((total_revenue - total_cost) / total_cost * 100
                                      if total_cost > 0 else 0)

            results.append({
                              "strategy": strategy.name,
                              "cost_24mo": total_cost,
                              "revenue_gain": total_revenue,
                              "months_to_10x": months_to_target or (n_months + 1),
                              "pct_reached_target": pct_reached,
                              "risk_level": risk,
                              "roi_pct": roi,
                              "final_users_median": result.summary["p50_final_users"],
                              "final_mrr_mean": result.summary["mean_final_mrr"],
                              "description": strategy.description,
            })

        return pd.DataFrame(results)

    def print_comparison(self, df):
              """Print formatted strategy comparison matrix."""
              print("\n" + "=" * 85)
              print("  STRATEGY TRADE-OFF MATRIX - PATH TO 10x")
              print("=" * 85)

        for _, row in df.iterrows():
                      print("  %-22s Cost: $%10s  Revenue: $%10s  Months: %4.0f  Risk: %-6s  ROI: %6.0f%%" % (
                                        row["strategy"],
                                        "{:,.0f}".format(row["cost_24mo"]),
                                        "{:,.0f}".format(row["revenue_gain"]),
                                        row["months_to_10x"],
                                        row["risk_level"],
                                        row["roi_pct"],
                      ))

        print("=" * 85 + "\n")

        best = df.loc[df["roi_pct"].idxmax()]
        fastest = df.loc[df["months_to_10x"].idxmin()]
        print("  Highest ROI:    %s (%.0f%%)" % (best["strategy"], best["roi_pct"]))
        print("  Fastest to 10x: %s (%.0f months)" % (fastest["strategy"], fastest["months_to_10x"]))
        print("=" * 85 + "\n")


if __name__ == "__main__":
      matrix = TradeOffMatrix()
      matrix.load_default_strategies()
      results = matrix.evaluate()
      matrix.print_comparison(results)
