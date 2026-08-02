"""Data module initializer."""
from data.loader import DatasetLoader
from data.generator import generate_synthetic_dataset

__all__ = ["DatasetLoader", "generate_synthetic_dataset"]
