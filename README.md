# law-researcher-agent

Reusable legal research agent configuration for Claude Code. Focused on Austrian
and European law — statutory interpretation, case law analysis, regulatory
compliance, insurance contract review, and market comparison.

## Agents

| Agent              | Purpose                                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------------------ |
| `law-researcher`   | Legal research — statutory interpretation, case law, commentary, regulatory compliance                 |
| `insurance-broker` | Insurance contract analysis, AGB review, regulatory checks, market comparison (fiduciary duty to user) |

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — Python package manager

### Required system tools

These binaries must be on `PATH`.

| Tool        | Package       | Purpose                                             | Linux (apt)                  | macOS (brew)       | Windows (winget)   |
| ----------- | ------------- | --------------------------------------------------- | ---------------------------- | ------------------ | ------------------ |
| `pdftotext` | poppler-utils | PDF → Markdown extraction for contract/AGB archival | `sudo apt install poppler-utils` | `brew install poppler` | `winget install xpdf-utils` |

> **Note:** On Windows, `pdftotext` is shipped with
> [Xpdf command-line tools](https://www.xpdfreader.com/download.html).
> After installing via winget, ensure the installation directory is on `PATH`.

### Optional tools

| Tool        | Package                | Purpose                                                                 | Linux (apt)                                                    | macOS (brew)                                           | Windows (winget)              |
| ----------- | ---------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------ | ----------------------------- |
| `tesseract` | tesseract-ocr          | OCR for scanned/image-only PDFs                                         | `sudo apt install tesseract-ocr tesseract-ocr-deu libglib2.0-bin` | `brew install tesseract && brew install tesseract-lang` | `winget install tesseract-ocr` |
| `gio`       | glib2 / libglib2.0-bin | Desktop-trash integration (Linux/GNOME only; falls back to `os.unlink`) | (included in libglib2.0-bin above)                             | —                                                      | —                              |

> **Note:** German language data is bundled in the winget `tesseract-ocr` package.
> `gio` is not available on Windows — the tools fall back to `os.unlink`.

## Setup

```bash
# Clone and enter the repo
git clone https://github.com/lena-miyamoto/law-researcher-agent.git && cd law-researcher-agent

# Install Python dependencies (pytest, pymarkdownlnt)
uv sync
```

No runtime Python dependencies — only dev tooling. All PDF, OCR, and network
operations delegate to system binaries on `PATH`.

## Usage

All tools are invoked via `uv run <entry-point>` from the repo root.

### Local archive (`law-db/`)

All law-db usage instructions are owned by the law-db skill
(`.claude/skills/law-db/SKILL.md`). Invoke via `Skill: "law-db"` or
consult the skill file directly. Do not duplicate law-db commands
outside the skill — the skill is the single source of truth.

### Development

```bash
uv run test          # Run test suite
uv run lint-md       # Lint Markdown files
uv run lint-md --fix # Auto-fix lint violations
```

## Archive structure

`law-db/` is gitignored, auto-created on first use, and accessed exclusively
through `uv run` tools. Direct filesystem access is forbidden.

| Category      | Layout                  | Contents                                     |
| ------------- | ----------------------- | -------------------------------------------- |
| `searches/`   | `<topic>/`              | Machine-readable search JSON                 |
| `documents/`  | `<topic>/<identifier>/` | `metadata.json` + `abstract.txt`             |
| `fulltext/`   | `<topic>/<identifier>/` | `source.md` + `metadata.json`                |
| `guidelines/` | `<topic>/<title>/`      | `source.<lang>.md` with YAML frontmatter     |
| `web/`        | `<topic>/`              | Archived web pages                           |
| `contracts/`  | `<topic>/<identifier>/` | `metadata.json` + `source.pdf` + `source.md` |

## License

[0BSD](LICENSE)
