from __future__ import annotations

import unittest

from research.fmp_company_profiles import _map_fmp_profile


class TestFmpCompanyProfiles(unittest.TestCase):
    def test_map_fmp_profile_basic(self) -> None:
        payload = {
            "companyName": "Tata Motors Limited",
            "symbol": "TTM",
            "sector": "Consumer Cyclical",
            "industry": "Auto Manufacturers",
            "mktCap": 1234567890,
            "pe": 12.34,
            "revenueTTM": 999999999,
            "fullTimeEmployees": 482000,
        }

        result = _map_fmp_profile("ttm", payload)

        self.assertEqual(result["ticker"], "TTM")
        self.assertEqual(result["name"], "Tata Motors Limited")
        self.assertEqual(result["sector"], "Consumer Cyclical")
        self.assertEqual(result["industry"], "Auto Manufacturers")
        self.assertEqual(result["market_cap"], "1234567890")
        self.assertEqual(result["pe"], 12.34)
        self.assertEqual(result["revenue"], "999999999")
        self.assertEqual(result["employees"], "482000")

    def test_map_fmp_profile_handles_missing_fields(self) -> None:
        payload = {}

        result = _map_fmp_profile("aapl", payload)

        self.assertEqual(result["ticker"], "AAPL")
        self.assertEqual(result["name"], "AAPL")
        self.assertIsNone(result["sector"])
        self.assertIsNone(result["industry"])
        self.assertIsNone(result["market_cap"])
        self.assertIsNone(result["pe"])
        self.assertIsNone(result["revenue"])
        self.assertIsNone(result["employees"])


if __name__ == "__main__":
    unittest.main()
