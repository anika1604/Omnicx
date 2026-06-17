"""
Fine-tune RoBERTa on emotion dataset for customer support sentiment.
Uses HuggingFace Trainer API.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)
from sklearn.metrics import accuracy_score, f1_score
import numpy as np
import torch

MODEL_NAME   = "cardiffnlp/twitter-roberta-base-sentiment-latest"
OUTPUT_PATH  = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'backend', 'ml', 'sentiment', 'model')
)

# Label mapping — map emotion labels to our 4 classes
LABEL_MAP = {
    "sadness":  "negative",
    "joy":      "positive",
    "love":     "positive",
    "anger":    "frustrated",
    "fear":     "negative",
    "surprise": "neutral",
}
OUR_LABELS  = ["positive", "neutral", "negative", "frustrated"]
LABEL2ID    = {l: i for i, l in enumerate(OUR_LABELS)}
ID2LABEL    = {i: l for i, l in enumerate(OUR_LABELS)}


def load_and_prepare():
    print("Loading dair-ai/emotion dataset...")
    ds = load_dataset("dair-ai/emotion")

    def remap(example):
        original = ds["train"].features["label"].int2str(example["label"])
        mapped   = LABEL_MAP.get(original, "neutral")
        example["label"] = LABEL2ID[mapped]
        return example

    ds = ds.map(remap)
    print(f"Train: {len(ds['train'])} Validation: {len(ds['validation'])} Test: {len(ds['test'])}")
    return ds


def tokenize(ds, tokenizer):
    def tok(batch):
        return tokenizer(batch["text"], truncation=True, max_length=128)
    return ds.map(tok, batched=True)


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1":       f1_score(labels, preds, average="weighted"),
    }


def train():
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Training on: {device}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model     = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(OUR_LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,
    )

    ds  = load_and_prepare()
    ds  = tokenize(ds, tokenizer)
    dc  = DataCollatorWithPadding(tokenizer)

    args = TrainingArguments(
        output_dir=OUTPUT_PATH,
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        learning_rate=2e-5,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_steps=50,
        fp16=torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds["train"],
        eval_dataset=ds["validation"],
        tokenizer=tokenizer,
        data_collator=dc,
        compute_metrics=compute_metrics,
    )

    print("Starting fine-tuning...")
    trainer.train()

    print("Evaluating on test set...")
    results = trainer.evaluate(ds["test"])
    print(f"Test Accuracy: {results['eval_accuracy']:.3f}")
    print(f"Test F1: {results['eval_f1']:.3f}")

    trainer.save_model(OUTPUT_PATH)
    tokenizer.save_pretrained(OUTPUT_PATH)
    print(f"\n✅ Fine-tuned model saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    train()