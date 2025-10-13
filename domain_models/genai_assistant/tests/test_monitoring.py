import unittest
import time
from GenAI_Factory.domain_models.genai_assistant.monitoring.latency_monitor import LatencyMonitor
from GenAI_Factory.domain_models.genai_assistant.monitoring.cost_monitor import CostMonitor
from GenAI_Factory.domain_models.genai_assistant.monitoring.drift_monitor import DriftMonitor

class TestMonitoring(unittest.TestCase):

    def test_latency_monitor(self):
        """Test latency tracking and summary calculation."""
        monitor = LatencyMonitor()
        start_time = monitor.start_timer("test_metric")
        time.sleep(0.01)
        latency = monitor.stop_timer("test_metric", start_time)
        self.assertGreater(latency, 0.0)
        summary = monitor.get_summary()
        self.assertIn("test_metric", summary)

    def test_cost_monitor(self):
        """Test token usage and cost calculation."""
        monitor = CostMonitor()
        monitor.record_usage("gpt-4", 100, 200)
        report = monitor.get_report()
        expected_cost = (100 * 0.00003) + (200 * 0.00006)
        self.assertAlmostEqual(report["estimated_cost"], expected_cost)

    def test_drift_monitor(self):
        """Test query drift detection."""
        monitor = DriftMonitor(window_size=10)
        for i in range(10):
            monitor.add_query(f"This is a common query about AI. {i}")
        
        # Test with a similar query (no drift)
        result1 = monitor.check_drift("Another common query about AI.")
        self.assertFalse(result1["drift_detected"])
        
        # Test with a very different query (drift)
        result2 = monitor.check_drift("I want to know about ancient Roman history.")
        self.assertTrue(result2["drift_detected"])
