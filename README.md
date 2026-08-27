#### dataset_filechecker

# Dataset File Checker & Audit Remediation Utility

- dataset cleaning tool for CSV, TSV, JSON, and JSONL
- terminal-cli or Q&A-interactive
- checks include: broken rows, duplicate rows, near-dupliate rows, etc.
- Only import that is not python-standard-library is `pandas`

---

## Key Features

- **Format & Ingestion Diagnostics**: Detects malformed rows, mismatched delimiter counts, quote escaping issues, and JSON decode errors before loading.
- **Mixed Data Type Identification**: Inspects underlying Python types in `object` columns (e.g., detecting `int` mixed with `str`).
- **Comprehensive Summary Statistics**: Enriched metrics including null percentages, whitespace-only cell counts, zero counts, and cardinality.
- **Exact Duplicate Detection**: Fast 64-bit row-level object hashing to isolate duplicate clusters.
- **Near-Duplicate Fuzzy Matching**: Alphanumeric text normalization with exact Levenshtein edit distance and customizable similarity thresholds.
- **Train / Test Split Integrity (Part B)**: Read-only verification to catch cross-split data leakage, feature/schema divergence, and novel/unseen categorical values in test sets.
- **Interactive Q&A Remediation & Export**: Step-by-step terminal wizard to handle duplicates, coerce mixed types, drop null-heavy columns, and export to CSV/JSON.

---

## Requirements

- **Python 3.10+**
- **pandas**

```bash
pip install pandas
```

---

## Quick Start

### 1. Interactive Mode (Wizard)
Run the script with no arguments to launch the interactive prompt:

```bash
python dataset_checker.py
```

### 2. Single-File CLI Audit & Clean
Audit a dataset directly with CLI flags:

```bash
# Full audit with interactive remediation prompts
python dataset_checker.py -f data/customers.csv

# Read-only audit (non-interactive, skip cleaning)
python dataset_checker.py -f data/customers.json --non-interactive

# Audit with custom similarity threshold and skip near-duplicate scan
python dataset_checker.py -f data/customers.tsv --delimiter "\t" --skip-near-duplicates
```

### 3. Train / Test Split Leakage Check (Read-Only)
Verify split integrity without altering files:

```bash
python dataset_checker.py --train data/train.csv --test data/test.csv --target-column "is_churned"
```

---

## CLI Reference

| Flag | Description | Default |
| :--- | :--- | :--- |
| `-f, --file` | Path to single dataset (`.csv`, `.tsv`, `.txt`, `.json`, `.jsonl`) | `None` |
| `--train` | Path to reference training partition (train/test audit mode) | `None` |
| `--test` | Path to evaluation testing partition (train/test audit mode) | `None` |
| `--target-column` | Target label column to exclude from categorical shift checks | `None` |
| `-o, --out` | Destination output file path for cleaned data | `None` |
| `--format` | Export format (`csv` or `json`) | `None` |
| `--delimiter` | Delimiter override for CSV/TSV input | Inferred |
| `--similarity-threshold` | Fuzzy near-duplicate similarity threshold (`0.0` – `1.0`) | `0.85` |
| `--skip-near-duplicates` | Skip Levenshtein near-duplicate calculation | `False` |
| `--non-interactive` | Run read-only audit without launching the cleaning wizard | `False` |

---

## Architecture Overview

```text
                       ┌──────────────────────────────────────────┐
                       │        CLI / Execution Router            │
                       └────────────────────┬─────────────────────┘
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
    ┌──────────────────────┐                                  ┌──────────────────────┐
    │  Single-File Workflow│                                  │ Train/Test Pair Mode │
    └──────────┬───────────┘                                  └──────────┬───────────┘
               │                                                         │
  1. Ingestion & Format Parsing                              1. Schema Compatibility Check
  2. Malformed Row Diagnostics                               2. Target & Feature Alignment
  3. Column Typing & Mixed-Type Detection                    3. Contamination / Leakage Check
  4. Exact Duplicate Analysis (Hashing)                      4. Unseen Categorical Levels
  5. Near-Duplicate Analysis (Levenshtein)                               │
  6. Descriptive Summary Statistics                                      ▼
               │                                              [ Read-Only Terminal Report ]
               ▼
  7. Interactive Q&A Remediation Wizard
               │
               ▼
  8. Export (Cleaned CSV / JSON)
```

---

## License
MIT

#### Code & Documentation Support
Gemini
