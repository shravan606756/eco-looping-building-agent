import unittest
from optimizer.optimization_loop import OptimizationLoop
from config import BASELINE_OUTPUT


class TestOptimizationLoop(unittest.TestCase):

    def test_optimization_loop_instantiation(self):
        loop = OptimizationLoop()
        self.assertIsNotNone(loop.runner)
        self.assertIsNotNone(loop.agent)
        self.assertIsNotNone(loop.modifier)


if __name__ == "__main__":
    unittest.main()