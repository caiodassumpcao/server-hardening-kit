#!/usr/bin/env python3
"""Compara relatórios do Lynis (antes/depois) e gera um resumo em Markdown.

Estrutura esperada (criada por playbooks/audit.yml):

    reports/<host>/before/lynis-report.dat
    reports/<host>/after/lynis-report.dat

Uso:
    python scripts/lynis_report.py --reports-dir reports \
        --output docs/reports/lynis-comparison.md --update-readme README.md
    python scripts/lynis_report.py --reports-dir reports --summary --fail-under 80

Somente biblioteca padrão: roda no controller sem dependências extras.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

README_START = "<!-- LYNIS:START -->"
README_END = "<!-- LYNIS:END -->"


@dataclass
class LynisReport:
    """Subconjunto relevante de um lynis-report.dat."""

    hardening_index: int
    lynis_version: str = "?"
    os_name: str = "?"
    os_version: str = "?"
    tests_performed: int = 0
    warnings: dict[str, str] = field(default_factory=dict)
    suggestions: dict[str, str] = field(default_factory=dict)


@dataclass
class HostComparison:
    host: str
    before: LynisReport
    after: LynisReport

    @property
    def delta(self) -> int:
        return self.after.hardening_index - self.before.hardening_index

    @property
    def resolved_suggestions(self) -> list[str]:
        return sorted(set(self.before.suggestions) - set(self.after.suggestions))

    @property
    def resolved_warnings(self) -> list[str]:
        return sorted(set(self.before.warnings) - set(self.after.warnings))


def _parse_finding(value: str) -> tuple[str, str]:
    # Formato: TEST-ID|descrição|detalhes|solução|
    parts = value.split("|")
    test_id = parts[0].strip()
    description = parts[1].strip() if len(parts) > 1 else ""
    return test_id, description


def parse_report(text: str) -> LynisReport:
    """Interpreta o conteúdo de um lynis-report.dat (linhas chave=valor)."""
    values: dict[str, str] = {}
    warnings: dict[str, str] = {}
    suggestions: dict[str, str] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key == "warning[]":
            test_id, description = _parse_finding(value)
            warnings.setdefault(test_id, description)
        elif key == "suggestion[]":
            test_id, description = _parse_finding(value)
            suggestions.setdefault(test_id, description)
        else:
            values[key] = value

    if "hardening_index" not in values:
        raise ValueError("hardening_index not found — is this a complete lynis-report.dat?")

    # Versões do Lynis expõem a lista (tests_executed=ID|ID|) e/ou o total (lynis_tests_done=N).
    if "tests_executed" in values:
        tests_performed = len([t for t in values["tests_executed"].split("|") if t])
    else:
        done = values.get("lynis_tests_done", "0")
        tests_performed = int(done) if done.isdigit() else 0

    return LynisReport(
        hardening_index=int(values["hardening_index"]),
        lynis_version=values.get("lynis_version", "?"),
        os_name=values.get("os_name", "?"),
        os_version=values.get("os_version", "?"),
        tests_performed=tests_performed,
        warnings=warnings,
        suggestions=suggestions,
    )


def load_comparisons(reports_dir: Path) -> list[HostComparison]:
    comparisons = []
    for host_dir in sorted(p for p in reports_dir.iterdir() if p.is_dir()):
        before = host_dir / "before" / "lynis-report.dat"
        after = host_dir / "after" / "lynis-report.dat"
        if not (before.is_file() and after.is_file()):
            continue
        comparisons.append(
            HostComparison(
                host=host_dir.name,
                before=parse_report(before.read_text(encoding="utf-8", errors="replace")),
                after=parse_report(after.read_text(encoding="utf-8", errors="replace")),
            )
        )
    return comparisons


def render_summary(comparisons: list[HostComparison]) -> str:
    lines = [
        "| Host | SO | Lynis | Score antes | Score depois | Δ | Warnings | Sugestões |",
        "|---|---|---|:-:|:-:|:-:|:-:|:-:|",
    ]
    for c in comparisons:
        lines.append(
            f"| `{c.host}` | {c.after.os_name} {c.after.os_version} | {c.after.lynis_version} "
            f"| **{c.before.hardening_index}** | **{c.after.hardening_index}** | {c.delta:+d} "
            f"| {len(c.before.warnings)} → {len(c.after.warnings)} "
            f"| {len(c.before.suggestions)} → {len(c.after.suggestions)} |"
        )
    return "\n".join(lines)


def _bullet_list(ids: list[str], descriptions: dict[str, str]) -> list[str]:
    if not ids:
        return ["- _nenhum_"]
    return [f"- `{test_id}` — {descriptions.get(test_id, '')}".rstrip(" —") for test_id in ids]


def render_details(comparisons: list[HostComparison]) -> str:
    out = ["# Lynis — comparação antes/depois", "", render_summary(comparisons), ""]
    for c in comparisons:
        out += [
            f"## `{c.host}`",
            "",
            f"Hardening index: **{c.before.hardening_index} → {c.after.hardening_index}** ({c.delta:+d})",
            "",
            f"### Warnings resolvidos ({len(c.resolved_warnings)})",
            *_bullet_list(c.resolved_warnings, c.before.warnings),
            "",
            f"### Sugestões resolvidas ({len(c.resolved_suggestions)})",
            *_bullet_list(c.resolved_suggestions, c.before.suggestions),
            "",
            f"### Sugestões remanescentes ({len(c.after.suggestions)})",
            "",
            "Itens que o kit **não** aplica por decisão consciente (particionamento, senha de",
            "GRUB, AIDE, `kernel.modules_disabled`, `MaxSessions 2`...) ficam aqui, com a",
            "justificativa em [Fora de escopo](../CIS_MAPPING.md#fora-de-escopo-decisão-consciente).",
            "",
            *_bullet_list(sorted(c.after.suggestions), c.after.suggestions),
            "",
        ]
    return "\n".join(out)


def update_readme(readme: Path, summary: str) -> bool:
    content = readme.read_text(encoding="utf-8")
    start = content.find(README_START)
    end = content.find(README_END)
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"markers {README_START} / {README_END} not found in {readme}")
    new_content = content[: start + len(README_START)] + "\n" + summary + "\n" + content[end:]
    if new_content == content:
        return False
    readme.write_text(new_content, encoding="utf-8", newline="\n")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--output", type=Path, help="arquivo Markdown com o relatório detalhado")
    parser.add_argument("--update-readme", type=Path, help="README com os marcadores LYNIS:START/END")
    parser.add_argument("--summary", action="store_true", help="imprime a tabela-resumo no stdout")
    parser.add_argument("--fail-under", type=int, help="falha (exit 1) se algum score final ficar abaixo deste valor")
    args = parser.parse_args(argv)

    # O console do Windows (cp1252) não imprime "Δ"/"→" da tabela.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if not args.reports_dir.is_dir():
        print(f"error: {args.reports_dir} does not exist — run make audit-before / audit-after first", file=sys.stderr)
        return 2

    comparisons = load_comparisons(args.reports_dir)
    if not comparisons:
        print(f"error: no host in {args.reports_dir} has both before/ and after/ reports", file=sys.stderr)
        return 2

    summary = render_summary(comparisons)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_details(comparisons), encoding="utf-8", newline="\n")
        print(f"wrote {args.output}")
    if args.update_readme:
        changed = update_readme(args.update_readme, summary)
        print(f"{'updated' if changed else 'unchanged'} {args.update_readme}")
    if args.summary or not (args.output or args.update_readme):
        print(summary)

    if args.fail_under is not None:
        below = [c for c in comparisons if c.after.hardening_index < args.fail_under]
        for c in below:
            print(f"FAIL: {c.host} hardening index {c.after.hardening_index} < {args.fail_under}", file=sys.stderr)
        if below:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
