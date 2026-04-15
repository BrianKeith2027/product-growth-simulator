"""
Sensitivity Analysis — Tornado Chart & Lever Impact Ranking
============================================================
Performs one-at-a-time sensitivity analysis on growth levers to identify
which parameters have the highest marginal impact on reaching 10x targets.

Author: Brian Stratton
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
from copy import deepcopy
import logging

from ..simulation.growth_engine import GrowthEngine, GrowthLevers, SimulationConfig

logger = logging.getLogger(__name__)


@dataclass
class SensitivityResult:
      """Result for a single lever's sensitivity analysis."""
      lever_name: str
      base_value: float
      low_value: float
      high_value: float
      base_months_to_target: float
      low_months_to_target: float
      high_months_to_target: float
      impact_range: float  # high - low impact in months
    direction: str  # "positive" or "negative" (does increasing help?)


class SensitivityAnalyzer:
      """
          One-at-a-time sensitivity analysis for growth levers.

              Varies each growth lever independently while holding others constant
                  to measure marginal impact on time-to-target and final user count.

                      Usage:
                              analyzer = SensitivityAnalyzer(base_levers=GrowthLevers())
                                      results = analyzer.run_analysis()
                                              analyzer.print_tornado(results)
                                                  """

    LEVER_CONFIGS = {
              "monthly_churn_rate": {"variation": 0.40, "direction": "negative"},
              "viral_coefficient": {"variation": 0.50, "direction": "positive"},
              "activation_rate": {"variation": 0.25, "direction": "positive"},
              "arpu": {"variation": 0.30, "direction": "positive"},
              "monthly_new_users": {"variation": 0.30, "direction": "positive"},
              "upsell_rate": {"variation": 0.50, "direction": "positive"},
              "organic_pct": {"variation": 0.30, "direction": "positive"},
              "expansion_revenue_pct": {"variation": 0.40, "direction": "positive"},
    }

    def __init__(self, base_levers: GrowthLevers = None,
                                  config: SimulationConfig = None):
                                            self.base_levers = base_levers or GrowthLevers()
                                            self.config = config or SimulationConfig(n_simulations=5000)

    def _run_single_scenario(self, levers: GrowthLevers) -> float:
              """Run simulation and return median months to target."""
              engine = GrowthEngine(levers=levers, config=self.config)
              result = engine.run_simulation()
              if result.summary["median_months_to_target"] is not None:
                            return result.summary["median_months_to_target"]
                        return self.config.n_months + 1

    def run_analysis(self) -> List[SensitivityResult]:
              """
                      Run sensitivity analysis across all configured levers.

                              For each lever:
                                      1. Set lever to low value (base - variation%)
                                              2. Run simulation, record months to target
                                                      3. Set lever to high value (base + variation%)
                                                              4. Run simulation, record months to target
                                                                      5. Calculate impact range

                                                                              Returns:
                                                                                          List of SensitivityResult sorted by impact (highest first)
                                                                                                  """
        logger.info("Starting sensitivity analysis...")
        base_months = self._run_single_scenario(self.base_levers)
        results = []

        for lever_name, config in self.LEVER_CONFIGS.items():
                      base_value = getattr(self.base_levers, lever_name)
                      variation = config["variation"]

            # Low scenario
                      low_levers = deepcopy(self.base_levers)
            low_value = base_value * (1 - variation)
            setattr(low_levers, lever_name, low_value)
            low_months = self._run_single_scenario(low_levers)

            # High scenario
            high_levers = deepcopy(self.base_levers)
            high_value = base_value * (1 + variation)
            setattr(high_levers, lever_name, high_value)
            high_months = self._run_single_scenario(high_levers)

            impact_range = abs(high_months - low_months)

            results.append(SensitivityResult(
                              lever_name=lever_name,
                              base_value=base_value,
                              low_value=low_value,
                              high_value=high_value,
                              base_months_to_target=base_months,
                              low_months_to_target=low_months,
                              high_months_to_target=high_months,
                              impact_range=impact_range,
                              direction=config["direction"],
            ))

            logger.info(f"  {lever_name}: impact = {impact_range:.1f} months")

        results.sort(key=lambda x: x.impact_range, reverse=True)
        return results

    def to_dataframe(self, results: List[SensitivityResult]) -> pd.DataFrame:
              """Convert sensitivity results to a Pandas DataFrame."""
        records = []
        for r in results:
                      records.append({
                                        "lever": r.lever_name,
                                        "base_value": r.base_value,
                                        "low_value": r.low_value,
                                        "high_value": r.high_value,
                                        "base_months": r.base_months_to_target,
                                        "low_months": r.low_months_to_target,
                                        "high_months": r.high_months_to_target,
                                        "impact_months": r.impact_range,
                                        "direction": r.direction,
                      })
                  return pd.DataFrame(records)

    def print_tornado(self, results: List[SensitivityResult]) -> None:
              """Print formatted tornado chart to console."""
        print("\n" + "=" * 65)
        print("  SENSITIVITY ANALYSIS — PATH TO 10x")
        print("=" * 65)
        print(f"  {'Lever':<25} {'Impact':>10}   Visual")
          print("-" * 65)

        max_impact = results[0].impact_range if results else 1
        for r in results:
                      bar_len = int((r.impact_range / max_impact) * 30)
                      bar = "█" * bar_len
                      sign = "-" if r.direction == "negative" else "+"
                      print(f"  {r.lever_name:<25} {sign}{r.impact_range:>7.1f}mo   {bar}")

        print("-" * 65)
        if results:
                      top = results[0]
                      print(f"\n  Key Insight: {top.lever_name} has the highest leverage.")
                      print(f"  Optimizing it can shift the 10x timeline by {top.impact_range:.1f} months.")
                  print("=" * 65 + "\n")


if __name__ == "__main__":
      analyzer = SensitivityAnalyzer()
    results = analyzer.run_analysis()
    analyzer.print_tornado(results)
