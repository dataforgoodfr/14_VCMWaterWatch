"""Pytest configuration and shared fixtures."""
import logging
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def test_data_dir(project_root):
    """Return the test data directory."""
    return project_root / "data"


@pytest.fixture(autouse=True)
def _mock_prefect_logger():
    """Disable Prefect run loggers so get_run_logger() returns a null logger
    instead of raising MissingContextError outside a flow/task context."""
    flow_logger = logging.getLogger("prefect.flow_runs")
    task_logger = logging.getLogger("prefect.task_runs")
    flow_logger.disabled = True
    task_logger.disabled = True
    yield
    flow_logger.disabled = False
    task_logger.disabled = False
