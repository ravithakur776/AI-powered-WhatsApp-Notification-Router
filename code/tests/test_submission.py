"""Unit tests for SubmissionRunner and CSV validation logic."""

import asyncio
from pathlib import Path
import pytest
import pandas as pd
from src.submission_runner import SubmissionRunner, validate_submission_csv


def test_submission_runner_execution(tmp_path: Path):
    out_csv = tmp_path / "output.csv"
    runner = SubmissionRunner()
    
    async def _test():
        res_path = await runner.run_submission(output_csv_path=out_csv)
        assert res_path.exists()
        
        df = pd.read_csv(res_path)
        assert list(df.columns) == ["message_id", "action", "message_type", "reason", "confidence", "evidence_message_ids"]
        assert len(df) > 0
        assert validate_submission_csv(res_path, len(df)) is True

    asyncio.run(_test())


def test_csv_validation_invalid_action(tmp_path: Path):
    invalid_csv = tmp_path / "invalid_output.csv"
    df = pd.DataFrame([{
        "message_id": "M_1",
        "action": "invalid_action",
        "message_type": "test",
        "reason": "test",
        "confidence": 0.9,
        "evidence_message_ids": "none"
    }])
    df.to_csv(invalid_csv, index=False)

    with pytest.raises(ValueError, match="Invalid action"):
        validate_submission_csv(invalid_csv, 1)


def test_csv_validation_out_of_range_confidence(tmp_path: Path):
    invalid_csv = tmp_path / "invalid_conf.csv"
    df = pd.DataFrame([{
        "message_id": "M_1",
        "action": "notify",
        "message_type": "test",
        "reason": "test",
        "confidence": 1.5,  # Invalid confidence
        "evidence_message_ids": "none"
    }])
    df.to_csv(invalid_csv, index=False)

    with pytest.raises(ValueError, match="out of range"):
        validate_submission_csv(invalid_csv, 1)
