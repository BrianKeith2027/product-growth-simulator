"""
Growth Engine — Monte Carlo Simulation for Product Growth Modeling
==================================================================
Simulates product growth trajectories across multiple strategy combinations
using configurable AARRR funnel parameters and Monte Carlo sampling.

Author: Brian Stratton
"""

import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GrowthLevers:
      """Configuration for all growth levers in the AARRR funnel."""
      # Acquisition
      monthly_new_users: int = 1000
      cac: float = 50.0
      organic_pct: float = 0.30
      paid_conversion_rate: float = 0.03

    # Activation
      activation_rate: float = 0.60
      time_to_value_days: int = 3
      onboarding_completion: float = 0.70

    # Retention
      monthly_churn_rate: float = 0.05
      engagement_score: float = 0.65

    # Revenue
      arpu: float = 29.99
      upsell_rate: float = 0.08
      expansion_revenue_pct: float = 0.15

    # Referral
      viral_coefficient: float = 0.15
      referral_conversion_rate: float = 0.25


@dataclass
class SimulationConfig:
      """Configuration for Monte Carlo simulation parameters."""
      n_simulations: int = 10000
      n_months: int = 24
      target_multiplier: float = 10.0
      random_seed: Optional[int] = 42
      variation_pct: float = 0.15  # Parameter variation for Monte Carlo


@dataclass
class SimulationResult:
      """Container for simulation output data."""
      trajectories: np.ndarray = field(default_factory=lambda: np.array([]))
      revenue_trajectories: np.ndarray = field(default_factory=lambda: np.array([]))
      months_to_target: np.ndarray = field(default_factory=lambda: np.array([]))
      final_users: np.ndarray = field(default_factory=lambda: np.array([]))
      final_revenue: np.ndarray = field(default_factory=lambda: np.array([]))
      summary: Dict = field(default_factory=dict)


class GrowthEngine:
      """
          Monte Carlo simulation engine for product growth modeling.

              Simulates product growth across the AARRR funnel (Acquisition, Activation,
                  Retention, Revenue, Referral) using configurable parameters with statistical
                      variation to model uncertainty.

                          Usage:
                                  engine = GrowthEngine(levers=GrowthLevers(), config=SimulationConfig())
                                          result = engine.run_simulation()
                                                  engine.print_summary(result)
                                                      """

    def __init__(self, levers: GrowthLevers, config: SimulationConfig):
              self.levers = levers
              self.config = config
              if config.random_seed is not None:
                            np.random.seed(config.random_seed)
                        logger.info(f"GrowthEngine initialized: {config.n_simulations} simulations, "
                                                         f"{config.n_months} months, target={config.target_multiplier}x")

    def _sample_parameter(self, base_value: float, n_samples: int) -> np.ndarray:
              """Sample parameter values with normal distribution around base value."""
        std = base_value * self.config.variation_pct
        samples = np.random.normal(base_value, std, n_samples)
        return np.clip(samples, base_value * 0.5, base_value * 1.5)

    def _sample_rate(self, base_rate: float, n_samples: int) -> np.ndarray:
              """Sample rate parameters, clipped to [0, 1]."""
        std = base_rate * self.config.variation_pct
        samples = np.random.normal(base_rate, std, n_samples)
        return np.clip(samples, 0.01, 0.99)

    def run_simulation(self) -> SimulationResult:
              """
                      Run Monte Carlo growth simulation.

                              For each simulation iteration:
                                      1. Sample all growth lever parameters with variation
                                              2. Simulate month-by-month user growth through AARRR funnel
                                                      3. Calculate revenue at each timestep
                                                              4. Record trajectory and time-to-target

                                                                      Returns:
                                                                                  SimulationResult with all trajectories and summary statistics
                                                                                          """
        n_sims = self.config.n_simulations
        n_months = self.config.n_months
        levers = self.levers

        logger.info("Sampling growth lever parameters...")

        # Sample all parameters for all simulations at once
        new_users = self._sample_parameter(levers.monthly_new_users, n_sims)
        activation = self._sample_rate(levers.activation_rate, n_sims)
        churn = self._sample_rate(levers.monthly_churn_rate, n_sims)
        arpu = self._sample_parameter(levers.arpu, n_sims)
        viral_coeff = self._sample_rate(levers.viral_coefficient, n_sims)
        upsell = self._sample_rate(levers.upsell_rate, n_sims)
        expansion = self._sample_rate(levers.expansion_revenue_pct, n_sims)

        # Initialize trajectory arrays
        user_trajectories = np.zeros((n_sims, n_months + 1))
        revenue_trajectories = np.zeros((n_sims, n_months + 1))
        initial_users = levers.monthly_new_users * levers.activation_rate
        user_trajectories[:, 0] = initial_users

        logger.info("Running Monte Carlo simulation...")

        for month in range(1, n_months + 1):
                      prev_users = user_trajectories[:, month - 1]

            # Acquisition: new users * activation rate
                      acquired = new_users * activation

            # Referral: existing users * viral coefficient
                      referred = prev_users * viral_coeff

            # Retention: existing users * (1 - churn)
                      retained = prev_users * (1 - churn)

            # Total active users this month
                      total_users = retained + acquired + referred
                      user_trajectories[:, month] = np.maximum(total_users, 0)

            # Revenue: active users * ARPU * (1 + upsell + expansion)
                      monthly_revenue = total_users * arpu * (1 + upsell + expansion)
                      revenue_trajectories[:, month] = monthly_revenue

        # Calculate target metrics
        target_users = initial_users * self.config.target_multiplier
        final_users = user_trajectories[:, -1]
        final_revenue = revenue_trajectories[:, -1]

        # Find month where target is first reached for each simulation
        months_to_target = np.full(n_sims, n_months + 1)  # default: never reached
        for sim in range(n_sims):
                      reached = np.where(user_trajectories[sim, :] >= target_users)[0]
                      if len(reached) > 0:
                                        months_to_target[sim] = reached[0]

                  # Build summary statistics
                  reached_mask = months_to_target <= n_months
        summary = {
                      "target_multiplier": self.config.target_multiplier,
                      "target_users": target_users,
                      "initial_users": initial_users,
                      "n_simulations": n_sims,
                      "pct_reached_target": float(reached_mask.mean() * 100),
                      "median_months_to_target": float(np.median(months_to_target[reached_mask]))
                          if reached_mask.any() else None,
                      "mean_final_users": float(final_users.mean()),
                      "p10_final_users": float(np.percentile(final_users, 10)),
                      "p50_final_users": float(np.percentile(final_users, 50)),
                      "p90_final_users": float(np.percentile(final_users, 90)),
                      "mean_final_mrr": float(final_revenue.mean()),
                      "p10_final_mrr": float(np.percentile(final_revenue, 10)),
                      "p90_final_mrr": float(np.percentile(final_revenue, 90)),
                      "growth_multiple_median": float(np.median(final_users / initial_users)),
        }

        logger.info(f"Simulation complete. {summary['pct_reached_target']:.1f}% "
                                         f"of simulations reached {self.config.target_multiplier}x target.")

        return SimulationResult(
                      trajectories=user_trajectories,
                      revenue_trajectories=revenue_trajectories,
                      months_to_target=months_to_target,
                      final_users=final_users,
                      final_revenue=final_revenue,
                      summary=summary,
        )

    def print_summary(self, result: SimulationResult) -> None:
              """Print formatted simulation summary to console."""
              s = result.summary
              print("\n" + "=" * 60)
              print(f"  GROWTH SIMULATION SUMMARY — {s['target_multiplier']:.0f}x TARGET")
              print("=" * 60)
              print(f"  Simulations Run:        {s['n_simulations']:,}")
              print(f"  Initial Active Users:   {s['initial_users']:,.0f}")
              print(f"  Target Users:           {s['target_users']:,.0f}")
              print(f"  % Reached Target:       {s['pct_reached_target']:.1f}%")
              if s['median_months_to_target']:
                            print(f"  Median Months to 10x:   {s['median_months_to_target']:.1f}")
                        print("-" * 60)
        print(f"  Final Users (P10):      {s['p10_final_users']:,.0f}")
        print(f"  Final Users (Median):   {s['p50_final_users']:,.0f}")
        print(f"  Final Users (P90):      {s['p90_final_users']:,.0f}")
        print(f"  Growth Multiple (Med):  {s['growth_multiple_median']:.1f}x")
        print("-" * 60)
        print(f"  Final MRR (Mean):       ${s['mean_final_mrr']:,.0f}")
        print(f"  Final MRR (P10-P90):    ${s['p10_final_mrr']:,.0f} - ${s['p90_final_mrr']:,.0f}")
        print("=" * 60 + "\n")


def run_default_simulation():
      """Run simulation with default parameters and print results."""
    levers = GrowthLevers()
    config = SimulationConfig()
    engine = GrowthEngine(levers=levers, config=config)
    result = engine.run_simulation()
    engine.print_summary(result)
    return result


if __name__ == "__main__":
      run_default_simulation()
