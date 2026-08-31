#### dataset_filechecker

# Dataset File Checker & Audit Remediation Utility

- dataset cleaning tool for CSV, TSV, JSON, and JSONL
- terminal-cli or Q&A-interactive
- checks include: broken rows, duplicate rows, near-duplicate rows, etc.
- Only required import that is not python-standard-library is `pandas` (one other, prompted, is optional)

### Features:
- Consolidate negative/0 classification label (many fields to one)
- Consolidate positive/1 classification label (many fields to one)
- Reads csv or json (pandas is flexible)
- Checks and can remove exactly identical (e.g.) 'text' value rows
- Checks and can remove or allow inspection and decision for Fuzzy-Near-Identical (e.g.) 'text' value rows

---

## Key Features

- **Format & Ingestion Diagnostics**: Detects malformed rows, mismatched field counts, invalid quoting, and line-specific JSON decode syntax errors before loading into DataFrames.
- **Mixed Data Type Identification**: Detects columns with generic `object` dtypes containing multiple conflicting Python types (e.g., `int` mixed with `str` or `dict`) and provides breakdown percentages.
- **Enriched Summary Statistics**: Extended `.describe()` metrics tracking total nulls, null percentages, whitespace-only cells, zero counts, and unique value cardinality.
- **Exact Duplicate Detection (Hashing)**: Fast, vectorized 64-bit integer object hashing (`pandas.util.hash_pandas_object`) to cluster and count identical records.
- **Near-Duplicate Fuzzy Matching (Exact Levenshtein)**: Text normalization (alphanumeric lowercase) combined with an optimized Wagner-Fischer edit distance algorithm, strictness tiers, and pairwise diff breakdowns.
- **Train / Test Split Integrity (Part B)**: Read-only verification to catch cross-partition data leakage, schema/feature misalignment, and novel/unseen categorical values in evaluation splits.
- **Interactive Remediation Wizard**:
  - Deduplication strategy selection (`first`, `last`, `none`).
  - Near-duplicate pair resolution (auto-resolve or manual keep/drop/ignore per pair).
  - Mixed-type column coercion (`numeric`, `string`, or `keep`).
  - Missing-value column drop thresholds with live impact preview.
  - **Interactive Remediation Wizard**:
    - Deduplication strategy selection (`first`, `last`, `none`).
    - Near-duplicate pair resolution (auto-resolve or manual keep/drop/ignore per pair).
    - Mixed-type column coercion (`numeric`, `string`, or `keep`).
    - Multi-class label binarization into binary `[0, 1]` classes.
    - Missing-value column drop thresholds with live impact preview.
- **Sanitized Multi-Format Export**: Serializes to CSV (custom delimiters), pretty JSON, or line-delimited JSON (JSONL), automatically collapsing internal newlines to preserve strict single-line record integrity.

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
Run the script without arguments to enter the interactive step-by-step wizard:

```bash
python dataset_checker.py
```

### 2. Single-File CLI Audit & Clean
Audit a dataset directly using CLI flags:

```bash
# Full audit with interactive remediation prompts
python dataset_checker.py -f data/customers.csv

# Read-only audit (non-interactive, skipping remediation and export)
python dataset_checker.py -f data/customers.json --non-interactive

# Fast audit skipping the Levenshtein near-duplicate check
python dataset_checker.py -f data/customers.tsv --delimiter "\t" --skip-near-duplicates
```

### 3. Train / Test Split Leakage & Integrity Check (Read-Only)
Verify schema alignment and cross-split contamination without modifying either file:

```bash
python dataset_checker.py --train data/train.csv --test data/test.csv --target-column "is_churned"
```

---

## CLI Reference

| Flag | Description | Default |
| :--- | :--- | :--- |
| `-f, --file` | Path to single dataset (`.csv`, `.tsv`, `.txt`, `.json`, `.jsonl`) | `None` |
| `--train` | Path to reference training partition (Train/Test verification mode) | `None` |
| `--test` | Path to evaluation testing partition (Train/Test verification mode) | `None` |
| `--target-column` | Target label column to exclude from novel categorical shift checks | `None` |
| `-o, --out` | Destination output file path for cleaned dataset | `None` |
| `--format` | Target export format: `csv`, `json`, `jsonl` | `jsonl` |
| `--delimiter` | Delimiter override for CSV/TSV input | Inferred (`None`) |
| `--similarity-threshold` | Near-duplicate similarity threshold (`0.0` – `1.0`) | `0.85` |
| `--skip-near-duplicates` | Skip Levenshtein near-duplicate distance evaluation entirely | `False` |
| `--non-interactive` | Run read-only terminal audit report without launching remediation wizard | `False` |

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
  4. Exact Duplicate Analysis (64-bit Hash)                  4. Unseen Categorical Levels
  5. Near-Duplicate Analysis (Wagner-Fischer)                            │
  6. Descriptive Summary Statistics                                      ▼
               │                                              [ Read-Only Terminal Report ]
               ▼
  7. Interactive Q&A Remediation Wizard
               │
               ▼
  8. Export (Sanitized CSV / JSON / JSONL)
```

---
#### Code & Documentation Support
Gemini

## License
MIT
