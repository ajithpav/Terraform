provider "oci" {
  region = "us-ashburn-1" # Change the region as per your requirement
}

# Create a Virtual Cloud Network (VCN)
resource "oci_core_vcn" "my_vcn" {
  cidr_block = "10.0.0.0/16"
  display_name = "my_vcn"
  compartment_id = "<your_compartment_ocid>"
}

# Create an Internet Gateway for public access
resource "oci_core_internet_gateway" "my_internet_gateway" {
  compartment_id = oci_core_vcn.my_vcn.compartment_id
  vcn_id         = oci_core_vcn.my_vcn.id
  display_name   = "my_internet_gateway"
  enabled        = true
}

# Create a public subnet
resource "oci_core_subnet" "public_subnet" {
  cidr_block       = "10.0.1.0/24"
  vcn_id           = oci_core_vcn.my_vcn.id
  compartment_id   = oci_core_vcn.my_vcn.compartment_id
  display_name     = "public_subnet"
  availability_domain = "AD-1" # Change according to your availability domain
  route_table_id   = oci_core_default_route_table.my_route_table.id
  security_list_ids = [oci_core_default_security_list.my_security_list.id]
  dhcp_options_id  = oci_core_vcn.my_vcn.default_dhcp_options_id
  prohibit_public_ip_on_vnic = false
}

# Create a private subnet
resource "oci_core_subnet" "private_subnet" {
  cidr_block       = "10.0.2.0/24"
  vcn_id           = oci_core_vcn.my_vcn.id
  compartment_id   = oci_core_vcn.my_vcn.compartment_id
  display_name     = "private_subnet"
  availability_domain = "AD-1" # Change according to your availability domain
  route_table_id   = oci_core_default_route_table.my_route_table.id
  security_list_ids = [oci_core_default_security_list.my_security_list.id]
  dhcp_options_id  = oci_core_vcn.my_vcn.default_dhcp_options_id
  prohibit_public_ip_on_vnic = true
}

# Create Route Table for Internet Gateway (Public Subnet)
resource "oci_core_default_route_table" "my_route_table" {
  compartment_id = oci_core_vcn.my_vcn.compartment_id
  vcn_id         = oci_core_vcn.my_vcn.id

  route_rules {
    destination = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.my_internet_gateway.id
  }
}

# Create Security List for both subnets
resource "oci_core_default_security_list" "my_security_list" {
  compartment_id = oci_core_vcn.my_vcn.compartment_id
  vcn_id         = oci_core_vcn.my_vcn.id

  # Ingress rules (allowing inbound traffic)
  ingress_security_rules {
    protocol = "6" # TCP
    source = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }

  # Egress rules (allowing outbound traffic)
  egress_security_rules {
    protocol = "all"
    destination = "0.0.0.0/0"
  }
}
