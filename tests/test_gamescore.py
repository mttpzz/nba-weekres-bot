import unittest

from nba_weekres.gamescore import game_score


class TestGameScore(unittest.TestCase):
    def test_known_statline(self):
        # 30 PTS, 11/20 FG, 6/8 FT, 2 OREB, 6 DREB, 2 STL, 8 AST, 1 BLK, 2 PF, 3 TOV
        row = {
            "points": 30,
            "fgm": 11,
            "fga": 20,
            "ftm": 6,
            "fta": 8,
            "offReb": 2,
            "defReb": 6,
            "steals": 2,
            "assists": 8,
            "blocks": 1,
            "pFouls": 2,
            "turnovers": 3,
        }
        self.assertAlmostEqual(game_score(row), 27.3, places=4)

    def test_missing_fields_default_to_zero(self):
        self.assertEqual(game_score({}), 0)


if __name__ == "__main__":
    unittest.main()
