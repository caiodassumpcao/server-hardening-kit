import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import lynis_report  # noqa: E402

BEFORE = """\
# Lynis Report
lynis_version=3.1.2
os_name=Ubuntu
os_version=24.04
hardening_index=58
tests_executed=SSH-7408|FIRE-4590|KRNL-6000|
warning[]=FIRE-4590|No firewall active|-|-|
suggestion[]=SSH-7408|Consider hardening SSH configuration|AllowTcpForwarding (set YES to NO)|-|
suggestion[]=SSH-7408|Consider hardening SSH configuration|MaxAuthTries (set 6 to 3)|-|
suggestion[]=KRNL-6000|One or more sysctl values differ from the scan profile|-|-|
suggestion[]=ACCT-9628|Enable auditd to collect audit information|-|-|
"""

AFTER = """\
lynis_version=3.1.2
os_name=Ubuntu
os_version=24.04
hardening_index=81
lynis_tests_done=4
suggestion[]=BOOT-5122|Set a password on GRUB boot loader|-|-|
"""


def write_host(root: Path, host: str, before: str = BEFORE, after: str = AFTER) -> None:
    for label, content in (("before", before), ("after", after)):
        target = root / host / label
        target.mkdir(parents=True)
        (target / "lynis-report.dat").write_text(content, encoding="utf-8")


def test_parse_report_extracts_score_and_dedupes_findings():
    report = lynis_report.parse_report(BEFORE)
    assert report.hardening_index == 58
    assert report.tests_performed == 3
    assert set(report.warnings) == {"FIRE-4590"}
    # duas linhas SSH-7408 viram um único achado
    assert set(report.suggestions) == {"SSH-7408", "KRNL-6000", "ACCT-9628"}


def test_parse_report_requires_hardening_index():
    with pytest.raises(ValueError):
        lynis_report.parse_report("lynis_version=3.1.2\n")


def test_comparison_delta_and_resolved(tmp_path):
    write_host(tmp_path, "lab-01")
    [comparison] = lynis_report.load_comparisons(tmp_path)
    assert comparison.delta == 23
    assert comparison.resolved_warnings == ["FIRE-4590"]
    assert comparison.resolved_suggestions == ["ACCT-9628", "KRNL-6000", "SSH-7408"]


def test_hosts_without_both_reports_are_skipped(tmp_path):
    write_host(tmp_path, "complete")
    (tmp_path / "partial" / "before").mkdir(parents=True)
    (tmp_path / "partial" / "before" / "lynis-report.dat").write_text(BEFORE, encoding="utf-8")
    assert [c.host for c in lynis_report.load_comparisons(tmp_path)] == ["complete"]


def test_update_readme_replaces_only_between_markers(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("intro\n<!-- LYNIS:START -->\nold\n<!-- LYNIS:END -->\noutro\n", encoding="utf-8")
    assert lynis_report.update_readme(readme, "| new |") is True
    assert readme.read_text(encoding="utf-8") == "intro\n<!-- LYNIS:START -->\n| new |\n<!-- LYNIS:END -->\noutro\n"
    # idempotente
    assert lynis_report.update_readme(readme, "| new |") is False


def test_main_fail_under_gate(tmp_path, capsys):
    write_host(tmp_path, "lab-01")
    assert lynis_report.main(["--reports-dir", str(tmp_path), "--summary", "--fail-under", "80"]) == 0
    assert lynis_report.main(["--reports-dir", str(tmp_path), "--fail-under", "90"]) == 1
    assert "**58** | **81** | +23" in capsys.readouterr().out
