# AI Agent Terraform — Infrastructure Experiments

Terraform configurations for experimental AI-agent API infrastructure. The repository contains account configuration under `accounts/`, environment configuration under `environments/`, and CI workflows under `.github/workflows/`.

> **Status:** The original README says `main` is out of date. Treat the default branch as an unverified historical snapshot; inspect branches and provider versions before using any configuration.

## Read-only validation workflow

Install a compatible Terraform CLI locally, then inspect the intended configuration directory. For example:

```sh
cd environments/swarms-aws-agent-api/dev/us-east-1
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
```

`terraform init` may download providers/modules, and `terraform validate` may require them. Review the source and provider constraints before executing these commands. If provider access or credentials are unavailable, record the validation as **blocked**, not passing.

**Do not run** `terraform apply`, `terraform destroy`, `terraform import`, or any state-changing operation as part of a documentation or syntax-check sprint.

## Review before any deployment

1. Confirm the intended branch, account, region, workspace, and cloud identity.
2. Inspect all modules, provider constraints, backend settings, and remote state access.
3. Check for hard-coded credentials, overly broad IAM permissions, and public ingress.
4. Run formatting, initialization with backend disabled, and validation in a disposable environment.
5. Require an independently reviewed plan, explicit cost approval, and human authorization before any deployment.

The example above is a suggested validation procedure, **not** a claim that this repository has passed validation. CI configuration and the environment's actual cloud permissions must be reviewed separately.

## Project directories

- `accounts/mdupont/` — account-level Terraform files
- `environments/swarms-aws-agent-api/dev/us-east-1/` — development environment files
- `.github/workflows/` — validation and security-related automation

For a modern deployment, first evaluate the latest maintained branch and upstream dependencies instead of assuming the default branch is production-ready.
