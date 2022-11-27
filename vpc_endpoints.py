from pulumi_aws import ec2
from pulumi import ResourceOptions
from settings import deployment_region, endpoint_services, general_tags
from vpc import demo_vpc, demo_private_subnets


# Create a shared security group for all AWS services VPC endpoints:
vpc_endpoints_sg = ec2.SecurityGroup("aws-vpc-endpoints-sg",
    description="Shared security groups for AWS services VPC endpoints",
    vpc_id=demo_vpc.id,
    tags={**general_tags, "Name": "aws-vpc-endpoints-sg"}
)

inbound_endpoints_cidrs = ec2.SecurityGroupRule("inbound-vpc-endpoint-cidrs",
    type="ingress",
    from_port=443,
    to_port=443,
    protocol="tcp",
    cidr_blocks=["0.0.0.0/0"],
    security_group_id=vpc_endpoints_sg.id
)

outbound_endpoints_cidrs = ec2.SecurityGroupRule("outbound-vpc-endpoint-cidrs",
    type="egress",
    to_port=0,
    protocol="-1",
    from_port=0,
    cidr_blocks=["0.0.0.0/0"],
    security_group_id=vpc_endpoints_sg.id
)

# Create VPC endpoints:
endpoints = []
for service in endpoint_services:
    if service == "s3":
        enable_dns = False
    else:
        enable_dns = True
    endpoints.append(ec2.VpcEndpoint(f"{service.replace('.','-')}-vpc-endpoint",
        vpc_id = demo_vpc.id,
        service_name = f"com.amazonaws.{deployment_region}.{service}",
        vpc_endpoint_type = "Interface",
        subnet_ids = [s.id for s in demo_private_subnets],
        security_group_ids = [vpc_endpoints_sg.id],
        private_dns_enabled = enable_dns,
        tags = {**general_tags, "Name": f"{service.replace('.','-')}-vpc-endpoint"},
        opts = ResourceOptions(
            depends_on=[vpc_endpoints_sg],
            parent=demo_vpc)
        ))