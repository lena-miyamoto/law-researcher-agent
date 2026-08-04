# law-researcher-agent

Reusable legal research agent configuration for Claude Code. Focused on Austrian
and European law — statutory interpretation, case law analysis, regulatory
compliance, insurance contract review, and market comparison.

## Skills

| Skill            | User-invocable | Purpose                                                                                                                        |
| ---------------- | :------------: | ------------------------------------------------------------------------------------------------------------------------------ |
| `explain-law`    |      Yes       | Explain an Austrian or EU law or case: fetch the official text, archive it, summarize key points, answer follow-up questions   |
| `law-db`         |       No       | Access the law-db archive — search, query, archive, validate. Every read/write to the local archive must go through this skill |
| `compress-skill` |      Yes       | Compress instruction `.md` files to cut token cost while keeping meaning exact                                                 |
| `optimize-repo`  |      Yes       | Audit and clean up instruction, skill, and agent files: cut redundancy, restore source-of-truth ownership                      |

Source of truth: `.claude/skills/<name>/SKILL.md`. `.github/skills/` are thin wrappers.

## Agents

| Agent              | Purpose                                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------------------ |
| `law-researcher`   | Legal research — statutory interpretation, case law, commentary, regulatory compliance                 |
| `insurance-broker` | Insurance contract analysis, AGB review, regulatory checks, market comparison (fiduciary duty to user) |

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager. Reads `.python-version` (3.12)
  and installs the correct Python automatically — no separate Python install needed.

### Required system tools

These binaries must be on `PATH`.

| Tool        | Package       | Purpose                                             | Linux (apt)                      | macOS (brew)           | Windows (winget)            |
| ----------- | ------------- | --------------------------------------------------- | -------------------------------- | ---------------------- | --------------------------- |
| `pdftotext` | poppler-utils | PDF → Markdown extraction for contract/AGB archival | `sudo apt install poppler-utils` | `brew install poppler` | `winget install xpdf-utils` |

> **Note:** On Windows, `pdftotext` is shipped with
> [Xpdf command-line tools](https://www.xpdfreader.com/download.html).
> After installing via winget, ensure the installation directory is on `PATH`.

### Optional tools

| Tool        | Package                | Purpose                                                                 | Linux (apt)                                                       | macOS (brew)                                            | Windows (winget)               |
| ----------- | ---------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------ |
| `tesseract` | tesseract-ocr          | OCR for scanned/image-only PDFs                                         | `sudo apt install tesseract-ocr tesseract-ocr-deu libglib2.0-bin` | `brew install tesseract && brew install tesseract-lang` | `winget install tesseract-ocr` |
| `gio`       | glib2 / libglib2.0-bin | Desktop-trash integration (Linux/GNOME only; falls back to `os.unlink`) | (included in libglib2.0-bin above)                                | —                                                       | —                              |

> **Note:** German language data is bundled in the winget `tesseract-ocr` package.
> `gio` is not available on Windows — the tools fall back to `os.unlink`.

## Setup

```bash
# Clone and enter the repo
git clone https://github.com/lena-miyamoto/law-researcher-agent.git && cd law-researcher-agent

# uv reads .python-version and installs Python 3.12 automatically,
# then creates a venv and installs dependencies (pytest, pymarkdownlnt)
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

## Environment setup

This repo is a Claude Code agent configuration. You need Claude Code, uv, and a
model provider. Python is managed automatically by uv via `.python-version`.

### 1. Claude Code

| Platform             | Command                                           |
| -------------------- | ------------------------------------------------- |
| macOS, Linux         | `curl -fsSL https://claude.ai/install.sh \| bash` |
| Windows (PowerShell) | `irm https://claude.ai/install.ps1 \| iex`        |

Native installs auto-update in the background. Verify with `claude --version`.

### 2. uv

| Platform | Command                                            |
| -------- | -------------------------------------------------- |
| Windows  | `winget install --id=astral-sh.uv -e`              |
| macOS    | `brew install uv`                                  |
| Linux    | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

Or via pip: `pip install uv`.

### 3. Python (via uv)

The repo ships a `.python-version` file pinning Python 3.12. `uv` reads it and
installs the correct version on first use — no manual Python install needed.

```bash
uv python install   # one-time: install Python 3.12
uv sync             # create venv + install dependencies
```

### 4. Model provider (DeepSeek)

#### Create an account

Sign up at [platform.deepseek.com/sign_up](https://platform.deepseek.com/sign_up).
You can register with an email address, a Google account, or a GitHub account.

#### Get an API key

After signing in, go to [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)
and click **"Create new API key"**. Give it a name and copy the key — it is shown
only once. Do not share the key or commit it to version control.

DeepSeek's API is pay-as-you-go. New accounts typically receive free credits to
start. Top up on the [billing page](https://platform.deepseek.com/top_up) if needed.

#### Configure Claude Code

Set the base URL and API key. Replace `<your-key>` with the key from the step above.

```bash
export DEEPSEEK_API_KEY="<your-key>"
export DEEPSEEK_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_DEFAULT_FABLE_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
export CLAUDE_CODE_DISABLE_1M_CONTEXT=1
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export DISABLE_GROWTHBOOK=1

claude
```

## License

[0BSD](LICENSE)
