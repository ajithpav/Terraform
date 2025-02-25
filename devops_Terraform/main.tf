provider "aws" {
  region = "eu-north-1"
}

# Create a VPC (Virtual Private Cloud)
resource "aws_vpc" "my_vpc" {
  cidr_block       = "172.31.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support = true
  tags = {
    Name = "my_vpc"
  }
}

# Create an Internet Gateway for public subnet
resource "aws_internet_gateway" "my_internet_gateway" {
  vpc_id = aws_vpc.my_vpc.id
  tags = {
    Name = "my_internet_gateway"
  }
}

# Create a public subnet
resource "aws_subnet" "public_subnet" {
  vpc_id     = aws_vpc.my_vpc.id
  cidr_block = "172.31.0.0/24"
  map_public_ip_on_launch = true
  availability_zone = "eu-north-1a"
  tags = {
    Name = "public_subnet"
  }
}

# Create a private subnet
resource "aws_subnet" "private_subnet" {
  vpc_id     = aws_vpc.my_vpc.id
  cidr_block = "172.31.1.0/24"
  availability_zone = "eu-north-1a"
  tags = {
    Name = "private_subnet"
  }
}

# Create a route table for the public subnet
resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.my_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.my_internet_gateway.id
  }
  tags = {
    Name = "public_route_table"
  }
}

# Associate the route table with the public subnet
resource "aws_route_table_association" "public_route_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_route_table.id
}

# Create a security group to allow SSH and HTTP access
resource "aws_security_group" "my_security_group" {
  vpc_id = aws_vpc.my_vpc.id
  name   = "my_security_group"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "my_security_group"
  }
}

# Create the EC2 instance
resource "aws_instance" "ajithdroidal_instance" {
  ami           = "ami-08eb150f611ca277f"
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public_subnet.id
  security_groups = [aws_security_group.my_security_group.name]
  key_name      = "ajithdroidal"  # Use your own key pair

  tags = {
    Name = "ajithdroidal_instance"
  }

  associate_public_ip_address = true

  # For instance monitoring (disabled in your instance)
  monitoring = false

  user_data = <<-EOF
              #!/bin/bash
              apt update -y
              apt upgrade -y
              EOF
}
