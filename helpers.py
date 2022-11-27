from pulumi_aws import iam
import json
import pulumi

"""
Helper functions
"""

def create_policy(name: str, policy_doc: str) -> iam.Policy:
    with open(f"controllers_iam_policies/{policy_doc}") as policy_file:
        policy_json = policy_file.read()

        policy = iam.Policy(f"{name}",
            policy=policy_json
        )
        return policy

def create_iam_role(name: str, principle_key: str ,principle_value: str, policy_arns: list=None) -> iam.Role:
    role = iam.Role(name, name=name, assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowAssumeRole",
                "Effect": "Allow",
                "Principal": {
                    f"{principle_key}": f"{principle_value}",
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }))
    if policy_arns is not None:
        for i, policy in enumerate(policy_arns):
            rpa = iam.RolePolicyAttachment(f"{name}-policy-{i}",
                policy_arn=policy,
                role=role.id)
    return role

# Create OIDC roles for service account, here using all and apply method to concatinate pulumi outputs needed to get OIDC provider details
def create_oidc_role(name: str, namespace: str, oidc_arn: str, oidc_url: str, svc_account_name: str, policy_arns: list=None) -> iam.Role:

    service_account_name = f"system:serviceaccount:{namespace}:{svc_account_name}"
 
    oidc_role = iam.Role(name, name=name, assume_role_policy=pulumi.Output.all(oidc_arn, oidc_url).apply(
        lambda args: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Federated": args[0],
                        },
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Condition": {
                            "StringEquals": {f"{args[1]}:sub": service_account_name},
                        },
                    }
                ],
            })))
    if policy_arns is not None:
        for i, policy in enumerate(policy_arns):
            rpa = iam.RolePolicyAttachment(f"{name}-policy-{i}",
                policy_arn=policy,
                role=oidc_role.id)
    else: pass
    return oidc_role