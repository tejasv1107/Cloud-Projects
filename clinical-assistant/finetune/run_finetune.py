"""
Launch a Bedrock Custom Model fine-tuning job on Amazon Nova Micro.

Base model ID: amazon.nova-micro-v1:0:128k

COST WARNING (as of 2026):
- Training cost: roughly $0.01-0.02 per 1K training tokens.
  For 500 examples averaging 1500 tokens each over 2 epochs = ~1.5M tokens,
  expected training cost is ~$15-30.
- Fine-tuned models REQUIRE Provisioned Throughput to invoke. No on-demand.
  See manage_throughput.py for provisioning and deletion.
"""
import boto3
import argparse
import json
import time
import uuid


def create_finetune_role(iam, account_id, role_name, bucket_name):
    """Create the IAM role Bedrock needs to read training data and write output."""
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {"aws:SourceAccount": account_id},
            },
        }],
    }

    s3_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*",
            ],
        }],
    }

    try:
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
        )
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="s3-access",
            PolicyDocument=json.dumps(s3_policy),
        )
        print(f"Created role: {role['Role']['Arn']}")
        time.sleep(10)
        return role["Role"]["Arn"]
    except iam.exceptions.EntityAlreadyExistsException:
        role = iam.get_role(RoleName=role_name)
        print(f"Role exists: {role['Role']['Arn']}")
        return role["Role"]["Arn"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True, help="S3 bucket with training data")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument(
        "--base-model",
        default="amazon.nova-micro-v1:0:128k",
        help="Base model to fine-tune",
    )
    parser.add_argument("--job-name", default=None)
    parser.add_argument("--custom-model-name", default=None)
    parser.add_argument("--epochs", default="2")
    parser.add_argument("--learning-rate", default="0.000001")
    parser.add_argument("--batch-size", default="1")
    args = parser.parse_args()

    sts = boto3.client("sts", region_name=args.region)
    account_id = sts.get_caller_identity()["Account"]

    iam = boto3.client("iam")
    role_arn = create_finetune_role(
        iam,
        account_id,
        "clinical-asst-bedrock-finetune-role",
        args.bucket,
    )

    bedrock = boto3.client("bedrock", region_name=args.region)

    unique = str(uuid.uuid4())[:8]
    job_name = args.job_name or f"clinical-sum-job-{unique}"
    model_name = args.custom_model_name or f"clinical-sum-model-{unique}"

    print(f"\nStarting fine-tuning job: {job_name}")
    print(f"Custom model name: {model_name}")
    print(f"Base model: {args.base_model}")
    print(f"Hyperparameters: epochs={args.epochs}, lr={args.learning_rate}, batch={args.batch_size}")

    response = bedrock.create_model_customization_job(
        jobName=job_name,
        customModelName=model_name,
        roleArn=role_arn,
        baseModelIdentifier=args.base_model,
        customizationType="FINE_TUNING",
        trainingDataConfig={
            "s3Uri": f"s3://{args.bucket}/train/train.jsonl",
        },
        validationDataConfig={
            "validators": [
                {"s3Uri": f"s3://{args.bucket}/validation/validation.jsonl"}
            ]
        },
        outputDataConfig={
            "s3Uri": f"s3://{args.bucket}/output/",
        },
        hyperParameters={
            "epochCount": args.epochs,
            "batchSize": args.batch_size,
            "learningRate": args.learning_rate,
        },
    )

    print(f"\nJob ARN: {response['jobArn']}")
    print("\nMonitor progress:")
    print(
        f"  aws bedrock get-model-customization-job "
        f"--job-identifier {response['jobArn']} --region {args.region}"
    )
    print("\nOr watch all jobs:")
    print(f"  aws bedrock list-model-customization-jobs --region {args.region}")
    print("\nExpected training time: 30-90 min for Nova Micro with ~500 examples")
    print("\nAfter completion, get the custom model ARN:")
    print(f"  aws bedrock list-custom-models --region {args.region}")


if __name__ == "__main__":
    main()
