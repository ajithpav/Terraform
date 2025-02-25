# AWS VPC & EC2 Setup with Terraform

This Terraform script provisions an AWS infrastructure including a VPC, public and private subnets, an internet gateway, security groups, and an EC2 instance.

## 🚀 Setup Steps
1. **Install Terraform**: [Download Here](https://developer.hashicorp.com/terraform/downloads)
2. **Configure AWS CLI**: `aws configure`
3. **Initialize Terraform**: `terraform init`
4. **Plan Deployment**: `terraform plan`
5. **Apply Configuration**: `terraform apply -auto-approve`
6. **Destroy Resources (Optional)**: `terraform destroy -auto-approve`

## 🔧 Resources Created
- **VPC**: `172.31.0.0/16`
- **Subnets**:
  - Public: `172.31.0.0/24` (Public IP enabled)
  - Private: `172.31.1.0/24`
- **Internet Gateway**: For external access.
- **Security Group**: Allows SSH (22) & HTTP (80).
- **EC2 Instance**:
  - **AMI**: `ami-08eb150f611ca277f`
  - **Type**: `t3.micro`
  - **Key Pair**: `ajithdroidal` (replace accordingly)
  - **User Data**: Runs system updates on launch.

## ⚠️ Notes
- Update `key_name` with your actual AWS key.
- Modify **AMI ID** as per your region.
- **Public subnet** allows open SSH & HTTP (`0.0.0.0/0`), restrict if needed.

---

👤 **Author:** Ajith    
🌎 **GitHub:** [github.com/ajith](https://github.com/ajith)  
