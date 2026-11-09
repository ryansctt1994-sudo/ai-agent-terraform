# Terraform review validation and deployment boundary

This repository contains exploratory Terraform and Packer configurations.
Passing formatting, source checks, or `terraform validate` is **not**
approval to deploy or evidence that an AWS design is secure or operational.
Historical design discussion is preserved outside executable `.tf` files.

## Checked-in review workflow

`.github/workflows/terraform-validate.yml` runs source-only review jobs:

- Compare directories containing checked-in `.tf` files with the CI module
  matrix using `python3 scripts/check_terraform_roots.py`; run its offline
  Python regression tests so new module directories cannot quietly escape
  coverage.
- Run `terraform fmt -check -recursive` to reject formatting drift.
- In **each** configured module directory, run
  `terraform init -backend=false -input=false -no-color` followed by
  `terraform validate -no-color`. Disabling backend initialization prevents
  connecting to configured remote state during this check; provider/plugin
  initialization may still require network downloads.

The matrix currently covers these module directories:

1. `accounts/mdupont`
2. `environments/swarms-aws-agent-api/dev/us-east-1`
3. `environments/swarms-aws-agent-api/dev/us-east-1/components/machine_image`

## Toolchain version and compatibility review

CI currently pins **Terraform 1.10.5** via `hashicorp/setup-terraform@v3.1.2`
for formatting and validation. An earlier version of the workflow pinned
**Terraform 1.1.7**. This is a toolchain upgrade, not merely a formatting
repair. Before relying on the workflow for an approval decision, review the
module and provider-version constraints for compatibility and require actual
`terraform init` and `terraform validate` results from the pinned toolchain.
Agreement between two formatters alone does not establish provider validity
or deployment compatibility.

## Explicit exclusions and open risks

These review jobs must not execute `terraform plan`, `terraform apply`,
`packer build`, AWS mutations, or `call-swarms.yml`. The separate
operator-triggered `call-swarms.yml` workflow can interact with AWS SSM
and is **outside** this validation boundary.

The checked-in configuration contains account- or instance-specific
identifiers, AWS data lookups, and a Packer template. Terraform does not
validate Packer source semantics or the freshness of an AMI. Provider
permissions, secrets handling, IAM scope, remote-state safety, dependency
provenance, environmental drift, cloud cost, and deployment security
require separate review and appropriate authorization.

Reviewers should attach exact-head CI results or reproducible local
command receipts to the relevant pull request. Missing runs, formatting
passes, and static source checks must **not** be represented as successful
provider-backed Terraform validation.
