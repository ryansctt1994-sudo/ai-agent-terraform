"""Terraform root coverage is checked without initializing cloud providers."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_terraform_roots import check, ci_module_dirs, module_dirs


class TerraformRootsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "accounts/demo").mkdir(parents=True)
        (self.root / "accounts/demo/main.tf").write_text('terraform {}\n')
        (self.root / ".github/workflows").mkdir(parents=True)
        self.ci = self.root / ".github/workflows/terraform-validate.yml"
        self.ci.write_text(
            'strategy:\n  matrix:\n    module:\n'
            '      - accounts/demo\n'
        )

    def test_exact_module_inventory_passes(self):
        self.assertEqual(check(self.root, self.ci), [])
        self.assertEqual(module_dirs(self.root), {"accounts/demo"})
        self.assertEqual(ci_module_dirs(self.ci), {"accounts/demo"})

    def test_unchecked_module_is_detected(self):
        (self.root / "environments/dev").mkdir(parents=True)
        (self.root / "environments/dev/main.tf").write_text('terraform {}\n')
        self.assertIn("unvalidated Terraform module", check(self.root, self.ci)[0])

    def test_stale_matrix_entry_is_detected(self):
        self.ci.write_text(
            'strategy:\n  matrix:\n    module:\n'
            '      - accounts/demo\n      - environments/deleted\n'
        )
        self.assertTrue(any("no Terraform module" in issue for issue in check(self.root, self.ci)))

    def test_symlinked_module_is_rejected(self):
        outside = self.root / "external.txt"
        outside.write_text('terraform {}\n')
        (self.root / "accounts/demo/linked.tf").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlinked"):
            module_dirs(self.root)


if __name__ == "__main__":
    unittest.main()
