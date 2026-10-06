from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).parents[1]
RUNNER = ROOT / "checks" / "run_logged.py"


def test_run_logged_saves_stdout_and_stderr(tmp_path):
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--name", "sample check", "--log-dir", str(tmp_path),
         "--", sys.executable, "-c",
         "import sys; print('visible stdout'); print('visible stderr', file=sys.stderr)"],
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0
    assert "visible stdout" in result.stdout
    log = next(tmp_path.glob("*_sample-check_*.log")).read_text(encoding="utf-8")
    assert "visible stdout" in log and "visible stderr" in log
    assert "exit_code=0" in log


def test_run_logged_preserves_failure_exit_code(tmp_path):
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--name", "expected failure", "--log-dir", str(tmp_path),
         "--", sys.executable, "-c", "print('failure detail'); raise SystemExit(7)"],
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == 7
    log = next(tmp_path.glob("*_expected-failure_*.log")).read_text(encoding="utf-8")
    assert "failure detail" in log and "exit_code=7" in log


def test_check_workflows_upload_logs_and_compose_checks_mount_reports():
    import yaml

    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert services["reports-init"]["volumes"] == ["./reports:/reports"]
    for service_name in ["ports-check", "workspace-init", "integration-check", "airflow-check", "static-check"]:
        assert any(volume.startswith("./reports:/reports") for volume in services[service_name].get("volumes", []))
    for workflow in ["contracts.yml", "full-integration.yml", "kafka.yml", "ports.yml", "sql-connectors.yml"]:
        path = ROOT / ".github" / "workflows" / workflow
        content = path.read_text(encoding="utf-8")
        assert "checks/run_logged.py" in content
        assert "actions/upload-artifact@v4" in content
        assert "path: reports/" in content
