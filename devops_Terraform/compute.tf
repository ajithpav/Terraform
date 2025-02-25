# compute.tf

resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2 AMI (HVM), SSD Volume Type
  instance_type = "t2.micro"
  subnet_id     = aws_subnet.public.id
  
  vpc_security_group_ids = [aws_security_group.allow_ssh.id]
  
  tags = {
    Name = "WebServer"
  }
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.web_server.public_ip
}


#oracle

# resource "oraclepaas_instance" "example" {
#   availability_domain = "your_availability_domain"
#   compartment_id      = "ocid1.compartment.oc1..<unique_id>"
#   shape               = "VM.Standard2.1"
#   image               = "ocid1.image.oc1..<unique_id>"
#   subnet_id          = oraclepaas_subnet.example.id
# }