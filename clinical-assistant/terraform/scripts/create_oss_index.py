#!/usr/bin/env python3
"""
Creates the vector index in OpenSearch Serverless that Bedrock KB requires.
The AWS Terraform provider cannot create OSS indices directly.
"""
import argparse
import time
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--index-name", required=True)
    args = parser.parse_args()

    # Strip https:// if present
    host = args.endpoint.replace("https://", "").rstrip("/")

    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, args.region, "aoss")

    client = OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300,
    )

    index_body = {
        "settings": {
            "index.knn": True,
        },
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 1024,  # Titan Embed v2 default
                    "method": {
                        "engine": "faiss",
                        "name": "hnsw",
                        "space_type": "l2",
                    },
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
                "AMAZON_BEDROCK_METADATA": {"type": "text", "index": False},
            }
        },
    }

    # Retry loop - OSS takes a moment to be ready after creation
    for attempt in range(10):
        try:
            if client.indices.exists(args.index_name):
                print(f"Index {args.index_name} already exists")
                return
            response = client.indices.create(args.index_name, body=index_body)
            print(f"Created index: {response}")
            # Wait for index to propagate before Bedrock KB tries to use it
            time.sleep(60)
            return
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(15)

    raise RuntimeError("Failed to create OSS index after retries")


if __name__ == "__main__":
    main()
