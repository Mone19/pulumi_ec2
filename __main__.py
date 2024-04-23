import pulumi
import pulumi_aws as aws

# Set the AWS region to eu-central-1
aws.config.region = "eu-central-1"

# Create a new VPC
vpc = aws.ec2.Vpc("app-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    tags={'Name': 'app-vpc'}
)

# Create an Internet Gateway for the VPC
internet_gateway = aws.ec2.InternetGateway("app-gateway",
    vpc_id=vpc.id,
    tags={'Name': 'app-gateway'}
)

# Create a public Subnet within the VPC
subnet = aws.ec2.Subnet("app-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    availability_zone="eu-central-1a",
    tags={'Name': 'app-subnet'}
)

# Create a Route Table with routes for a public subnet
route_table = aws.ec2.RouteTable("app-route-table",
    vpc_id=vpc.id,
    routes=[{
        'cidr_block': '0.0.0.0/0',
        'gateway_id': internet_gateway.id,
    }],
    tags={'Name': 'app-route-table'}
)

# Associate the Subnet with the Route Table
route_table_association = aws.ec2.RouteTableAssociation("app-route-table-assoc",
    route_table_id=route_table.id,
    subnet_id=subnet.id
)

# The userdata script to install Docker and run the container
user_data = """#!/bin/bash
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user
docker run -dp 9898:9898 stefanprodan/podinfo
"""

# Security group to allow port 9898
security_group = aws.ec2.SecurityGroup('app-sg',
    description='Allow access to My App',
    vpc_id=vpc.id,

    ingress=[
        {
        'protocol': 'tcp',
        'from_port': 80,
        'to_port': 80,
        'cidr_blocks': ['0.0.0.0/0'],
    },
    {
        'protocol': 'tcp',
        'from_port': 22,
        'to_port': 22,
        'cidr_blocks': ['0.0.0.0/0'],
    },
    {
        'protocol': 'tcp',
        'from_port': 9898,
        'to_port': 9898,
        'cidr_blocks': ['0.0.0.0/0'],
    }
    ],
    egress=[{
        'protocol': '-1',
        'from_port': 0,
        'to_port': 0,
        'cidr_blocks': ['0.0.0.0/0'],
    }],
    tags={'Name': 'app-sg'}
)

# Create an EC2 instance within the Subnet
instance = aws.ec2.Instance('app-instance',
    ami='ami-0f673487d7e5f89ca',  # Amazon Linux 2 AMI (HVM) for eu-central-1
    instance_type='t2.micro',
    vpc_security_group_ids=[security_group.id],
    subnet_id=subnet.id,
    associate_public_ip_address=True,
    user_data=user_data,  # This will run the user_data script to install Docker and run the podinfo container
    tags={'Name': 'app-instance'}
)

# Export the public IP of the instance to access the application
pulumi.export('public_ip', instance.public_ip)
