import unittest

from src.resilience.backpressure import BackpressureError, BackpressureGuard
from src.resilience.retry import retry


class TestRetry(unittest.TestCase):
    def test_succeeds_without_retry_when_no_error(self):
        calls = []

        @retry(attempts=3, base_delay_seconds=0)
        def always_ok():
            calls.append(1)
            return "ok"

        self.assertEqual(always_ok(), "ok")
        self.assertEqual(len(calls), 1)

    def test_retries_then_succeeds(self):
        calls = []

        @retry(attempts=3, base_delay_seconds=0)
        def fails_twice_then_ok():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("transient")
            return "ok"

        self.assertEqual(fails_twice_then_ok(), "ok")
        self.assertEqual(len(calls), 3)

    def test_exhausts_attempts_and_raises_last_error(self):
        calls = []

        @retry(attempts=2, base_delay_seconds=0)
        def always_fails():
            calls.append(1)
            raise RuntimeError("permanent failure")

        with self.assertRaises(RuntimeError):
            always_fails()
        self.assertEqual(len(calls), 2)  # ไม่เกิน attempts ที่กำหนด


class TestBackpressureGuard(unittest.TestCase):
    def test_allows_up_to_capacity(self):
        guard = BackpressureGuard(max_concurrent=2)
        with guard, guard:  # ใช้ 2 slot พร้อมกันแบบ nested เพื่อจำลอง concurrent
            pass  # ไม่ควร raise

    def test_rejects_when_over_capacity(self):
        guard = BackpressureGuard(max_concurrent=1)
        guard.acquire()  # ใช้ slot เดียวไปแล้ว
        with self.assertRaises(BackpressureError):
            guard.acquire()
        guard.release()

    def test_release_frees_slot_for_next_request(self):
        guard = BackpressureGuard(max_concurrent=1)
        with guard:
            pass
        with guard:  # slot ต้องว่างแล้วหลัง context แรกจบ
            pass


if __name__ == "__main__":
    unittest.main()
