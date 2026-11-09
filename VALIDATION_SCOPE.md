# Terraform candidate validation and deployment boundary

This repository contains a historical exploratory configuration and a design
transcript moved out of `main.tf` by pending PR #1. Neither the notes nor a
passing syntax check are a reviewed AWS deployment plan.

The review workflow enumerates **all checked-in directories containing .tf
files** and checks each with `terraform init -backend=false -input=false` plus
`terraform validate`. It also checks formatting, with no `plan` or `apply`,
no AWS credentials and no change to remote state. A separate offline source
check refuses unvalidated module directories.

**Known open risks:** configuration includes hardcoded account- and
instance-specific identifiers, AWS data lookups and an operator-triggered
GitHub Actions SSM deployment workflow. Packer templates are not validated by
Terraform, and this pass does not qualify AMI freshness, provider permissions,
IAM scope, supply-chain provenance, environment drift, cost or live deployment.
Do not invoke `call-swarms.yml` as part of a validation run.

This is a draft candidate stacked on PR #1. CI success is a local configuration
claim only, and no PR is authorized to merge or deploy.
