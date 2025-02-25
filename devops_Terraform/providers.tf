# providers.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
}


# provider "oraclepaas" {
#   user            = "your_username"
#   password        = "your_password"
#   identity_domain = "your_identity_domain"
#   endpoint        = "https://api-z123.identity.oraclecloud.com"
# }