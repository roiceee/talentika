bucket         = "talentika-terraform-state"
key            = "app/prod/terraform.tfstate"
region         = "ap-southeast-1"
encrypt        = true
dynamodb_table = "talentika-terraform-locks"
