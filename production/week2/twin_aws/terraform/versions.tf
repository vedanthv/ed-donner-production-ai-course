terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region                  = var.aws_region
  profile                 = var.aws_profile != "" ? var.aws_profile : null
  shared_credentials_files = var.aws_shared_credentials_file != "" ? [var.aws_shared_credentials_file] : null
}

provider "aws" {
  alias                   = "us_east_1"
  region                  = var.aws_region
  profile                 = var.aws_profile != "" ? var.aws_profile : null
  shared_credentials_files = var.aws_shared_credentials_file != "" ? [var.aws_shared_credentials_file] : null
}