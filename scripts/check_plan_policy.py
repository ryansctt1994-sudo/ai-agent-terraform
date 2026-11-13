#!/usr/bin/env python3
"""Fail-closed subset of Terraform plan policies. No provider or cloud access."""
import json
import sys
from pathlib import Path

REQUIRED_TAGS = {"Environment", "Owner", "Project"}
TAGGED_TYPES = {"aws_instance", "aws_ebs_volume", "aws_s3_bucket"}
IAM_POLICY_TYPES = {"aws_iam_policy", "aws_iam_role_policy", "aws_iam_user_policy", "aws_iam_group_policy"}

def _items(value):
    return value if isinstance(value, list) else [value]

def inspect_plan(plan):
    if not isinstance(plan, dict) or not isinstance(plan.get("resource_changes"), list):
        return ["Plan has no valid resource_changes array (refusing ambiguous input)"]
    errors = []
    for entry in plan["resource_changes"]:
        if not isinstance(entry, dict) or entry.get("mode", "managed") != "managed":
            continue
        address = entry.get("address") or "<unnamed>"
        kind = entry.get("type", "")
        change = entry.get("change") or {}
        actions = change.get("actions", [])
        if not isinstance(actions, list):
            errors.append(f"{address}: malformed actions")
            continue
        if "delete" in actions:
            errors.append(f"{address}: destructive delete/replace requires independent approval")
        if not ({"create", "update"} & set(actions)):
            continue
        after = change.get("after")
        if not isinstance(after, dict):
            errors.append(f"{address}: no known proposed values")
            continue
        if kind in TAGGED_TYPES:
            tags = after.get("tags")
            if not isinstance(tags, dict) or not REQUIRED_TAGS.issubset(set(tags)):
                errors.append(f"{address}: required tags Environment, Owner, Project missing")
        if kind == "aws_ebs_volume" and after.get("encrypted") is not True:
            errors.append(f"{address}: EBS encryption not proven enabled")
        if kind == "aws_instance":
            for i, block in enumerate(_items(after.get("root_block_device", []))):
                if not isinstance(block, dict) or block.get("encrypted") is not True:
                    errors.append(f"{address}: root block device {i} encryption not proven")
        if kind == "aws_s3_bucket" and after.get("acl") in ("public-read", "public-read-write", "authenticated-read"):
            errors.append(f"{address}: public S3 canned ACL prohibited")
        if kind == "aws_s3_bucket_acl" and after.get("acl") not in (None, "private"):
            errors.append(f"{address}: public/non-private S3 ACL prohibited")
        if kind == "aws_s3_bucket_public_access_block":
            keys = ("block_public_acls", "ignore_public_acls", "block_public_policy", "restrict_public_buckets")
            if any(after.get(k) is not True for k in keys):
                errors.append(f"{address}: all four S3 public-access controls must be true")
        if kind in IAM_POLICY_TYPES:
            policy = after.get("policy")
            try:
                obj = json.loads(policy) if isinstance(policy, str) else policy
                if not isinstance(obj, dict):
                    raise ValueError("not an object")
                statements = _items(obj.get("Statement", []))
                for statement in statements:
                    if not isinstance(statement, dict):
                        raise ValueError("bad Statement")
                    if statement.get("Effect", "").lower() != "allow":
                        continue
                    for field in ("Action", "Resource"):
                        if "*" in _items(statement.get(field, [])):
                            errors.append(f"{address}: IAM Allow has wildcard {field}")
            except (ValueError, TypeError):
                errors.append(f"{address}: unparseable IAM policy JSON")
    return errors

def main():
    try:
        plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (IndexError, OSError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: no valid plan JSON: {exc}")
        return 2
    errors = inspect_plan(plan)
    for error in errors:
        print("BLOCKED:", error)
    if errors:
        return 1
    print("PASS: checked destructive changes and scoped AWS safety policies")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
