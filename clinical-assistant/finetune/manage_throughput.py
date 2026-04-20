"""
Helper to create and delete Provisioned Throughput for the fine-tuned Nova Micro model.

CRITICAL COST WARNING:
  Fine-tuned Nova models CANNOT be invoked on-demand.
  Provisioned Throughput is required and bills by the hour.
  Nova Micro no-commitment hourly pricing is the cheapest in the Nova family
  but still runs several dollars per hour — delete immediately after demo.

Usage:
  # Just before recording the demo:
  python manage_throughput.py create --model-arn <custom-model-arn>
  # ... record your demo ...
  python manage_throughput.py delete --throughput-arn <returned-pt-arn>
"""
import argparse
import boto3
import time


def create(model_arn: str, region: str, name: str):
    bedrock = boto3.client("bedrock", region_name=region)
    response = bedrock.create_provisioned_model_throughput(
        modelUnits=1,
        provisionedModelName=name,
        modelId=model_arn,
        # Omit commitmentDuration for no-commitment (hourly) pricing
    )
    throughput_arn = response["provisionedModelArn"]
    print(f"Provisioning started: {throughput_arn}")
    print("Waiting for status=InService (5-15 min typical)...")

    while True:
        status_resp = bedrock.get_provisioned_model_throughput(
            provisionedModelId=throughput_arn
        )
        status = status_resp["status"]
        print(f"  Status: {status}")
        if status == "InService":
            break
        if status == "Failed":
            raise RuntimeError("Provisioning failed")
        time.sleep(30)

    print(f"\n✅ READY. Use this ARN as the modelId for Converse API calls:")
    print(f"   {throughput_arn}")
    print(f"\nExport for the Streamlit app:")
    print(f"   export NOVA_FT_MODEL_ARN='{throughput_arn}'")
    print(f"\n⚠️  DELETE IMMEDIATELY AFTER DEMO:")
    print(f"   python manage_throughput.py delete --throughput-arn {throughput_arn}")
    return throughput_arn


def delete(throughput_arn: str, region: str):
    bedrock = boto3.client("bedrock", region_name=region)
    bedrock.delete_provisioned_model_throughput(provisionedModelId=throughput_arn)
    print(f"Deletion requested for {throughput_arn}")
    print("Billing stops once deletion completes (a few minutes).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["create", "delete"])
    parser.add_argument("--model-arn", help="Custom model ARN (for create)")
    parser.add_argument(
        "--throughput-arn", help="Provisioned throughput ARN (for delete)"
    )
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--name", default="clinical-asst-nova-pt")
    args = parser.parse_args()

    if args.action == "create":
        if not args.model_arn:
            parser.error("--model-arn required for create")
        create(args.model_arn, args.region, args.name)
    else:
        if not args.throughput_arn:
            parser.error("--throughput-arn required for delete")
        delete(args.throughput_arn, args.region)


if __name__ == "__main__":
    main()
