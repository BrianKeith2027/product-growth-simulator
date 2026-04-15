"""
Unit Economics Calculator - CAC, LTV, Payback Period
Author: Brian Stratton
"""

import numpy as np
import pandas as pd
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class UnitEconomicsCalculator:
      """Calculates core SaaS unit economics: CAC, LTV, payback period."""

    def __init__(self, cac=50.0, arpu=29.99, monthly_churn=0.05,
                                  gross_margin=0.75, upsell_rate=0.08, expansion_pct=0.15):
                                            self.cac = cac
                                            self.arpu = arpu
                                            self.monthly_churn = monthly_churn
                                            self.gross_margin = gross_margin
                                            self.upsell_rate = upsell_rate
                                            self.expansion_pct = expansion_pct

    def calculate_ltv(self, months=60):
              """Calculate Customer Lifetime Value over given horizon."""
              effective_arpu = self.arpu * (1 + self.upsell_rate + self.expansion_pct)
              values = [effective_arpu * self.gross_margin * ((1 - self.monthly_churn) ** m)
                        for m in range(months)]
              return sum(values)

    def calculate_payback_months(self):
              """Calculate months to recover CAC."""
              contribution = self.arpu * self.gross_margin
              return self.cac / contribution if contribution > 0 else float("inf")

    def calculate_all(self):
              """Calculate all unit economics metrics."""
              ltv = self.calculate_ltv()
              payback = self.calculate_payback_months()
              avg_lifetime = 1 / self.monthly_churn if self.monthly_churn > 0 else float("inf")
              return {
                  "cac": self.cac, "arpu": self.arpu,
                  "ltv": ltv, "ltv_to_cac": ltv / self.cac if self.cac > 0 else float("inf"),
                  "payback_months": payback, "avg_lifetime_months": avg_lifetime,
                  "monthly_gross_profit": self.arpu * self.gross_margin,
              }

    def print_report(self):
              """Print formatted unit economics report."""
              m = self.calculate_all()
              print("\n" + "=" * 50)
              print("  UNIT ECONOMICS REPORT")
              print("=" * 50)
              print("  CAC:            $%.2f" % m["cac"])
              print("  ARPU:           $%.2f/mo" % m["arpu"])
              print("  LTV:            $%.2f" % m["ltv"])
              print("  LTV:CAC Ratio:  %.1fx" % m["ltv_to_cac"])
              print("  Payback Period: %.1f months" % m["payback_months"])
              health = "Healthy" if m["ltv_to_cac"] >= 3 else "Warning"
              print("  Health:         %s" % health)
              print("=" * 50 + "\n")


if __name__ == "__main__":
      calc = UnitEconomicsCalculator()
      calc.print_report()
