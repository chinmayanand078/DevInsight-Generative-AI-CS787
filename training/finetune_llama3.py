"""Reference script for fine-tuning a Llama 3 model with custom review data.

"""
This is intentionally minimal but complete: it wires a dataset, tokenizer,
model, optimizer, and evaluation loop using Hugging Face transformers. It is
kept outside the runtime backend dependencies so CI stays lightweight; install
``training/requirements.txt`` before running.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)


@dataclass
class Sample:
    prompt: str
    completion: str


def tokenize_function(examples, tokenizer):
    """Tokenize paired prompt/completion examples for causal LM fine-tuning."""
    merged = [p + "\n" + c for p, c in zip(examples["prompt"], examples["completion"])]
    return tokenizer(merged, truncation=True, padding=False)


def build_trainer(dataset_path: str, model_name: str, output_dir: str, lr: float, epochs: int) -> Trainer:
    """Construct a Hugging Face Trainer for lightweight Llama 3 fine-tuning."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    dataset = load_dataset("json", data_files=dataset_path)
    tokenized = dataset.map(lambda ex: tokenize_function(ex, tokenizer), batched=True, remove_columns=dataset["train"].column_names)

    model = AutoModelForCausalLM.from_pretrained(model_name)

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=lr,
        num_train_epochs=epochs,
        fp16=False,
        logging_steps=10,
        save_strategy="epoch",
        evaluation_strategy="no",
    )

    return Trainer(
        model=model,
        args=args,
        train_dataset=tokenized["train"],
        data_collator=data_collator,
        tokenizer=tokenizer,
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the fine-tuning script."""
    parser = argparse.ArgumentParser(description="Fine-tune Llama3 on review/test data")
    parser.add_argument("--dataset", required=True, help="Path to JSONL with 'prompt' and 'completion' fields")
    parser.add_argument("--model", default="meta-llama/Meta-Llama-3-8B-Instruct", help="HF model id")
    parser.add_argument("--output", default="outputs/llama3-finetune", help="Directory for checkpoints")
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--epochs", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    """Run fine-tuning with the provided arguments and persist the model."""
    args = parse_args()
    trainer = build_trainer(args.dataset, args.model, args.output, args.lr, args.epochs)
    trainer.train()
    trainer.save_model(args.output)


if __name__ == "__main__":
    main()
