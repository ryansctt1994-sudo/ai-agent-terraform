import json
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_plan_policy import inspect_plan

def plan(*changes):
    return {"resource_changes": list(changes)}

def resource(kind, after=None, actions=None, address=None):
    return {"mode": "managed", "type": kind, "address": address or kind + ".demo",
            "change": {"actions": actions or ["create"], "after": after or {}}}

TAGS = {"Environment":"test","Owner":"qa","Project":"tinkerforge"}

class PlanPolicyTest(unittest.TestCase):
    def test_safe_private_s3_bucket(self):
        self.assertEqual(inspect_plan(plan(resource("aws_s3_bucket", {"acl":"private","tags":TAGS}))), [])
    def test_delete_and_replace_blocked(self):
        for actions in (["delete"], ["delete","create"], ["create","delete"]):
            with self.subTest(actions=actions):
                violations = inspect_plan(plan(resource("aws_instance", {"tags":TAGS}, actions)))
                self.assertTrue(any("destructive" in s for s in violations))
    def test_missing_tags_and_unencrypted_ebs_blocked(self):
        result = inspect_plan(plan(resource("aws_ebs_volume", {"encrypted":False,"tags":{"Owner":"qa"}})))
        self.assertTrue(any("required tags" in s for s in result))
        self.assertTrue(any("encryption" in s for s in result))
    def test_public_s3_acl_and_access_block_blocked(self):
        result = inspect_plan(plan(
            resource("aws_s3_bucket", {"tags":TAGS,"acl":"public-read"}),
            resource("aws_s3_bucket_public_access_block", {"block_public_acls": True})))
        self.assertEqual(sum("public" in s for s in result), 2)
    def test_wildcard_iam_action_and_resource_denied(self):
        policy = json.dumps({"Statement":[{"Effect":"Allow","Action":"*","Resource":"*"}]})
        errors = inspect_plan(plan(resource("aws_iam_policy", {"policy":policy})))
        self.assertTrue(any("wildcard Action" in s for s in errors))
        self.assertTrue(any("wildcard Resource" in s for s in errors))
    def test_restrictive_iam_allow_is_accepted(self):
        policy = json.dumps({"Statement":[{"Effect":"Allow","Action":"s3:GetObject",
                                            "Resource":"arn:aws:s3:::private-bucket/item"}]})
        self.assertEqual(inspect_plan(plan(resource("aws_iam_policy", {"policy":policy}))), [])
    def test_bad_plans_fail_closed(self):
        self.assertTrue(inspect_plan({}))
        self.assertTrue(inspect_plan({"resource_changes":"invalid"}))
        self.assertTrue(inspect_plan(plan(resource("aws_iam_policy", {"policy":"not-json"}))))

if __name__ == "__main__":
    unittest.main()
