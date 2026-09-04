"""Unit tests for Snakemake DAG integrity and rule syntax."""

import subprocess
import os
import pytest


def test_snakemake_dag_dry_run():
    """Verify that the full Snakemake workflow compiles without cyclic dependencies or syntax errors."""
    cmd = [
        "snakemake",
        "-n",
        "-s",
        "workflow/Snakefile",
        "--directory",
        "workflow",
        "all"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Snakemake dry-run failed with error:\n{res.stderr}\n{res.stdout}"
    assert "Building DAG of jobs..." in res.stdout or "Building DAG of jobs..." in res.stderr
