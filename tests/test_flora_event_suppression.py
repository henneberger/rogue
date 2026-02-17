import unittest

from fortress.engine import Game


class FloraEventSuppressionTests(unittest.TestCase):
    def test_flora_logs_are_not_recorded(self) -> None:
        g = Game(rng_seed=401)
        start_count = len(g.events)
        g._log("flora", "Wild onion reached mature.", 1)
        self.assertEqual(len(g.events), start_count)


if __name__ == "__main__":
    unittest.main()
