# Offline Terraform core-only fixture: no cloud credentials, network provider, or backend.
terraform {
  required_version = ">= 1.9.0, < 2.0.0"
}

resource "terraform_data" "approved_demo" {
  input = {
    environment = "isolated"
    owner       = "tinkerforge"
  }
}

output "fixture_status" {
  value = terraform_data.approved_demo.output.environment
}
