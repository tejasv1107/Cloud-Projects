"""
Prepare MTSamples data for Amazon Nova Micro fine-tuning.

Nova fine-tuning uses the Converse/Messages format (NOT the old Titan prompt/completion format).
Each line of JSONL is a conversation with 'system' and 'messages' fields.

Schema:
{
    "schemaVersion": "bedrock-conversation-2024",
    "system": [{"text": "..."}],
    "messages": [
        {"role": "user", "content": [{"text": "..."}]},
        {"role": "assistant", "content": [{"text": "..."}]}
    ]
}

Dataset: MTSamples from Kaggle (free)
  https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions
"""
import json
import os
import argparse
from pathlib import Path

import pandas as pd


SYSTEM_PROMPT = (
    "You are a clinical documentation assistant. Given a clinical note, "
    "produce a concise single-line description that captures the key clinical content."
)


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(text.split()).strip()


def build_nova_example(transcription: str, description: str) -> dict:
    return {
        "schemaVersion": "bedrock-conversation-2024",
        "system": [{"text": SYSTEM_PROMPT}],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": f"Summarize this clinical note:\n\n{clean_text(transcription)}"}
                ],
            },
            {
                "role": "assistant",
                "content": [{"text": clean_text(description)}],
            },
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", required=True, help="Path to mtsamples.csv")
    parser.add_argument("--output-dir", default="./output")
    parser.add_argument("--train-size", type=int, default=500)
    parser.add_argument("--val-size", type=int, default=50)
    parser.add_argument("--max-prompt-chars", type=int, default=6000)
    args = parser.parse_args()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input_csv)
    print(f"Loaded {len(df)} rows from {args.input_csv}")

    df = df.dropna(subset=["transcription", "description"])
    df["trans_len"] = df["transcription"].str.len()
    df["desc_len"] = df["description"].str.len()
    df = df[
        (df["trans_len"] > 200)
        & (df["trans_len"] < args.max_prompt_chars)
        & (df["desc_len"] > 20)
        & (df["desc_len"] < 500)
    ]
    print(f"After filtering: {len(df)} rows")

    if len(df) < args.train_size + args.val_size:
        raise ValueError(
            f"Not enough rows ({len(df)}) for train+val split "
            f"({args.train_size + args.val_size})"
        )

    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    train_df = df.iloc[: args.train_size]
    val_df = df.iloc[args.train_size : args.train_size + args.val_size]

    train_path = os.path.join(args.output_dir, "train.jsonl")
    val_path = os.path.join(args.output_dir, "validation.jsonl")

    with open(train_path, "w") as f:
        for _, row in train_df.iterrows():
            example = build_nova_example(row["transcription"], row["description"])
            f.write(json.dumps(example) + "\n")

    with open(val_path, "w") as f:
        for _, row in val_df.iterrows():
            example = build_nova_example(row["transcription"], row["description"])
            f.write(json.dumps(example) + "\n")

    print(f"\nWrote {len(train_df)} training examples -> {train_path}")
    print(f"Wrote {len(val_df)} validation examples -> {val_path}")

    print("\nSample record:")
    with open(train_path) as f:
        print(json.dumps(json.loads(f.readline()), indent=2)[:500])

    print("\nNext steps:")
    print(f"  aws s3 cp {train_path} s3://YOUR-FINETUNE-BUCKET/train/")
    print(f"  aws s3 cp {val_path} s3://YOUR-FINETUNE-BUCKET/validation/")


if __name__ == "__main__":
    main()
