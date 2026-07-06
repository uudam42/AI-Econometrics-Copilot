"""LaTeX source export generator.

Produces a standalone .tex file plus tables/ and figures/ directories.
The output compiles with pdflatex without additional packages beyond
standard TeX distributions (booktabs, graphicx, hyperref, geometry).
"""
from __future__ import annotations

import re
from pathlib import Path

from app.schemas.publication_export import PublicationExportConfig, FigureMetadata


def _escape_latex(text: str) -> str:
    specials = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for char, replacement in specials.items():
        text = text.replace(char, replacement)
    return text


def _md_table_to_latex(table_text: str) -> str:
    lines = [l.strip() for l in table_text.strip().split("\n") if l.strip().startswith("|")]
    if len(lines) < 2:
        return ""

    headers = [c.strip() for c in lines[0].strip("|").split("|")]
    rows = []
    for line in lines[1:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r"-+", c.replace(":", "")) for c in cells if c):
            continue
        rows.append(cells)

    ncols = len(headers)
    col_spec = "l" + "c" * (ncols - 1)
    tex_lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        rf"\begin{{tabular}}{{{col_spec}}}",
        r"\toprule",
        " & ".join(_escape_latex(h) for h in headers) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        padded = row + [""] * (ncols - len(row))
        tex_lines.append(" & ".join(_escape_latex(c) for c in padded[:ncols]) + r" \\")
    tex_lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(tex_lines)


def _md_to_latex_body(md: str) -> str:
    result: list[str] = []
    in_table = False
    table_lines: list[str] = []

    for line in md.split("\n"):
        stripped = line.strip()

        if stripped.startswith("|"):
            in_table = True
            table_lines.append(stripped)
            continue
        elif in_table:
            tex = _md_table_to_latex("\n".join(table_lines))
            if tex:
                result.append(tex)
            table_lines = []
            in_table = False

        if not stripped:
            result.append("")
            continue

        if stripped.startswith("# "):
            result.append(rf"\section{{{_escape_latex(stripped[2:])}}}")
        elif stripped.startswith("## "):
            result.append(rf"\subsection{{{_escape_latex(stripped[3:])}}}")
        elif stripped.startswith("### "):
            result.append(rf"\subsubsection{{{_escape_latex(stripped[4:])}}}")
        elif stripped.startswith("#### "):
            result.append(rf"\paragraph{{{_escape_latex(stripped[5:])}}}")
        elif stripped.startswith("**Table:"):
            title = stripped.strip("*").strip()
            result.append(rf"\noindent\textbf{{{_escape_latex(title)}}}")
        elif stripped.startswith("*Note:") or stripped.startswith("*Consistency") or stripped.startswith("*This appendix"):
            note = stripped.strip("*").strip()
            result.append(rf"\smallskip\noindent\textit{{\small {_escape_latex(note)}}}")
        elif stripped.startswith("- "):
            result.append(rf"\begin{{itemize}}")
            result.append(rf"  \item {_escape_latex(stripped[2:])}")
            result.append(rf"\end{{itemize}}")
        elif stripped.startswith("> "):
            result.append(rf"\begin{{quote}}")
            result.append(_escape_latex(stripped[2:]))
            result.append(rf"\end{{quote}}")
        else:
            bold_re = re.compile(r"\*\*(.+?)\*\*")
            converted = bold_re.sub(lambda m: rf"\textbf{{{_escape_latex(m.group(1))}}}", stripped)
            if converted == stripped:
                converted = _escape_latex(stripped)
            result.append(converted)

    if in_table and table_lines:
        tex = _md_table_to_latex("\n".join(table_lines))
        if tex:
            result.append(tex)

    return "\n".join(result)


def generate_latex(
    markdown_content: str,
    config: PublicationExportConfig,
    figures: list[FigureMetadata] | None = None,
    output_dir: Path | None = None,
) -> str:
    preamble_parts = [
        r"\documentclass[12pt,a4paper]{article}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage{booktabs}",
        r"\usepackage{graphicx}",
        r"\usepackage{hyperref}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{float}",
        "",
        rf"\title{{{_escape_latex(config.title)}}}",
    ]
    if config.author_name:
        preamble_parts.append(rf"\author{{{_escape_latex(config.author_name)}}}")
    if config.report_date:
        preamble_parts.append(rf"\date{{{_escape_latex(config.report_date.strftime('%B %d, %Y'))}}}")
    else:
        preamble_parts.append(r"\date{\today}")

    body = _md_to_latex_body(markdown_content)

    if figures and config.include_figures:
        body += "\n\n" + r"\clearpage" + "\n" + r"\section{Figures}" + "\n"
        for i, fig in enumerate(figures, 1):
            body += "\n".join([
                r"\begin{figure}[H]",
                r"\centering",
                rf"\includegraphics[width=0.85\textwidth]{{figures/{fig.filename}}}",
                rf"\caption{{{_escape_latex(fig.caption)}}}",
                rf"\label{{fig:{fig.figure_type}}}",
                r"\end{figure}",
                "",
            ])

    body += "\n\n" + (
        r"\vfill\noindent\textit{\small Disclaimer: The reported estimates "
        r"describe statistical associations and should not be interpreted as "
        r"causal effects without additional identification assumptions.}"
    )

    tex = "\n".join(preamble_parts) + "\n\n" + r"\begin{document}" + "\n"
    if config.include_cover_page:
        tex += r"\maketitle" + "\n"
    tex += "\n" + body + "\n\n" + r"\end{document}" + "\n"

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "tables").mkdir(exist_ok=True)
        (output_dir / "figures").mkdir(exist_ok=True)
        (output_dir / "appendix").mkdir(exist_ok=True)
        (output_dir / "main.tex").write_text(tex, encoding="utf-8")

        readme = (
            "# LaTeX Export\n\n"
            "Compile with: `pdflatex main.tex`\n\n"
            "Requirements: booktabs, graphicx, hyperref, geometry, float\n"
            "(included in standard TeX distributions like TeX Live or MiKTeX)\n\n"
            f"Title: {config.title}\n"
        )
        (output_dir / "README.md").write_text(readme, encoding="utf-8")

    return tex
