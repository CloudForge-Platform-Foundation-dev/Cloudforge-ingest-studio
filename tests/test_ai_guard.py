import unittest

from src.ai_guard.base import GuardDecisionSource
from src.ai_guard.guard import AIGuard
from src.ai_guard.local_backend import LocalRuleBackend


class FakeCloudBackend:
    """Backend จำลองสำหรับ test — คุมได้ว่าจะ 'ทำงานได้' หรือ 'ล่ม'"""

    def __init__(self, should_fail: bool, answer: str = "vm"):
        self.should_fail = should_fail
        self.answer = answer
        self.calls = 0

    def classify_asset_type(self, payload):
        self.calls += 1
        if self.should_fail:
            raise ConnectionError("simulated cloud outage / ไฟดับ / เน็ตล่ม")
        return self.answer


class TestAIGuardFailover(unittest.TestCase):
    def test_uses_cloud_when_available(self):
        cloud = FakeCloudBackend(should_fail=False, answer="database")
        guard = AIGuard(cloud_backend=cloud, local_backend=LocalRuleBackend())

        result = guard.classify_asset_type({"name": "irrelevant"})

        self.assertEqual(result.asset_type, "database")
        self.assertEqual(result.source, GuardDecisionSource.CLOUD)
        self.assertEqual(cloud.calls, 1)

    def test_falls_back_to_local_when_cloud_fails(self):
        cloud = FakeCloudBackend(should_fail=True)
        guard = AIGuard(cloud_backend=cloud, local_backend=LocalRuleBackend())

        result = guard.classify_asset_type({"name": "prod-mysql-primary"})

        # cloud ถูกลองเรียกก่อนเสมอ ถึงจะล่มก็ตาม
        self.assertEqual(cloud.calls, 1)
        self.assertEqual(result.source, GuardDecisionSource.LOCAL_FALLBACK)
        self.assertEqual(result.asset_type, "database")  # local เจอ keyword "mysql"

    def test_never_raises_even_when_cloud_completely_down(self):
        """หัวใจของ AI Guard: ไม่ว่า cloud จะพังแบบไหน ต้องไม่มี exception หลุดออกไป"""
        cloud = FakeCloudBackend(should_fail=True)
        guard = AIGuard(cloud_backend=cloud, local_backend=LocalRuleBackend())

        try:
            result = guard.classify_asset_type({"name": "some-s3-bucket"})
        except Exception as exc:  # noqa: BLE001 - ตั้งใจจับทุกอย่างเพื่อยืนยันว่าไม่มี exception เล็ดลอด
            self.fail(f"AIGuard ไม่ควร raise exception ออกมาเลย แต่ raise: {exc}")

        self.assertEqual(result.asset_type, "storage_bucket")
        self.assertEqual(result.source, GuardDecisionSource.LOCAL_FALLBACK)

    def test_default_uses_real_stub_cloud_backend_and_falls_back(self):
        """ใช้ CloudAIBackend ตัวจริง (ที่ยัง NotImplementedError อยู่) เพื่อยืนยันว่า
        ระบบ default (ยังไม่เสียบ client จริง) ก็ fallback ได้อย่างปลอดภัยเช่นกัน"""
        guard = AIGuard()  # ใช้ default CloudAIBackend + LocalRuleBackend

        result = guard.classify_asset_type({"description": "internal application service"})

        self.assertEqual(result.source, GuardDecisionSource.LOCAL_FALLBACK)
        self.assertEqual(result.asset_type, "application")


class TestLocalRuleBackend(unittest.TestCase):
    def setUp(self):
        self.backend = LocalRuleBackend()

    def test_classifies_vm_keywords(self):
        self.assertEqual(self.backend.classify_asset_type({"name": "web-ec2-instance-1"}), "vm")

    def test_classifies_network_keywords(self):
        self.assertEqual(self.backend.classify_asset_type({"desc": "main VPC subnet"}), "network_config")

    def test_defaults_to_application_when_no_keyword_matches(self):
        self.assertEqual(self.backend.classify_asset_type({"name": "xyz-123"}), "application")

    def test_ignores_none_values_in_payload(self):
        result = self.backend.classify_asset_type({"name": None, "type": "s3 bucket"})
        self.assertEqual(result, "storage_bucket")


if __name__ == "__main__":
    unittest.main()
