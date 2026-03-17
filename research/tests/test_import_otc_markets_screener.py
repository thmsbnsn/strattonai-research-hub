from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research.import_otc_markets_screener import load_otc_screener_csv


class TestImportOtcMarketsScreener(unittest.TestCase):
    def test_load_otc_screener_csv_parses_rows(self) -> None:
        csv_text = (
            "Symbol,Security Name,Tier,Price,Change %,Vol,Sec Type,Country,State\n"
            "FMCC,FREDDIE MAC,OTCQB,5.280000,-0.005650,2708777,Common Stock,USA,Virginia\n"
            "FNMA,FANNIE MAE,OTCQB,6.100000,0.014975,5262239,Common Stock,USA,Washington DC\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Stock_Screener.csv"
            path.write_text(csv_text, encoding="utf-8")
            rows = load_otc_screener_csv(path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].symbol, "FMCC")
        self.assertEqual(rows[1].symbol, "FNMA")
        self.assertAlmostEqual(rows[1].change_pct, 0.014975, places=8)

    def test_load_otc_screener_csv_filters_non_common_stock(self) -> None:
        csv_text = (
            "Symbol,Security Name,Tier,Price,Change %,Vol,Sec Type,Country,State\n"
            "WXYZ,TEST PREF,OTCQB,1.00,0.10,1000,Preferred Stock,USA,TX\n"
            "ABCD,TEST COMMON,OTCQX,1.25,0.05,2000,Common Stock,USA,CA\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Stock_Screener.csv"
            path.write_text(csv_text, encoding="utf-8")
            rows = load_otc_screener_csv(path)

        self.assertEqual([row.symbol for row in rows], ["ABCD"])


if __name__ == "__main__":
    unittest.main()

