"""Evaluation benchmark calculator computing F1, Precision, Recall, and Confusion Matrix."""

from typing import List, Dict, Any
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np


class RouterBenchmark:
    @staticmethod
    def evaluate_predictions(predictions: List[Dict[str, Any]], ground_truths: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates classification metrics comparing router predictions vs ground truth."""
        gt_map = {gt["message_id"]: gt["expected_action"] for gt in ground_truths if "expected_action" in gt}
        
        y_true = []
        y_pred = []

        for pred in predictions:
            msg_id = pred["message_id"]
            if msg_id in gt_map:
                y_true.append(gt_map[msg_id])
                y_pred.append(pred["action"])

        if not y_true:
            return {"status": "No overlapping ground truth labels found for evaluation."}

        labels = ["notify", "digest", "mute"]
        report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
        cm = confusion_matrix(y_true, y_pred, labels=labels)

        return {
            "total_evaluated": len(y_true),
            "macro_f1": round(report["macro avg"]["f1-score"], 4),
            "weighted_f1": round(report["weighted avg"]["f1-score"], 4),
            "accuracy": round(report["accuracy"], 4),
            "per_class_metrics": {
                label: {
                    "precision": round(report[label]["precision"], 4),
                    "recall": round(report[label]["recall"], 4),
                    "f1_score": round(report[label]["f1-score"], 4),
                    "support": report[label]["support"]
                }
                for label in labels if label in report
            },
            "confusion_matrix": {
                "labels": labels,
                "matrix": cm.tolist()
            }
        }
