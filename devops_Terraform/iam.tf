# iam.tf

resource "aws_iam_user" "example_user" {
  name = "example-user"

  tags = {
    Description = "Example IAM user created with Terraform"
  }
}

resource "aws_iam_policy" "example_policy" {
  name        = "example-policy"
  path        = "/"
  description = "Example IAM policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ec2:Describe*",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_user_policy_attachment" "example_attach" {
  user       = aws_iam_user.example_user.name
  policy_arn = aws_iam_policy.example_policy.arn
}


#oracle

# resource "oraclepaas_identity_user" "example" {
#   name           = "example-user"
#   compartment_id = "ocid1.compartment.oc1..<unique_id>"
#   description    = "Example user"
# }

# resource "oraclepaas_identity_group" "example" {
#   name           = "example-group"
#   compartment_id = "ocid1.compartment.oc1..<unique_id>"
#   description    = "Example group"
# }

# resource "oraclepaas_identity_policy" "example" {
#   name           = "example-policy"
#   compartment_id = "ocid1.compartment.oc1..<unique_id>"
#   description    = "Example policy"
#   statements     = ["Allow group example-group to manage all-resources in compartment example-compartment"]
# }