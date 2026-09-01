
"""
Dataset File Checker and Audit Remediation Utility.

# Architectural Scope and Technical Plan

### 1. automated, scalable data quality audit and cleaning framework

This module provides an automated, scalable data quality audit and cleaning
framework for CSV and JSON datasets. It performs structural parsing validation,
column type analysis, exact duplicate detection via hashing, near-duplicate
fuzzy matching via token-blocked edit distances, train/test split leakage
verification, and interactive remediation workflows.

Architecture: Flat-file, modular functional design.
Python Standard: 3.10+ (Zero non-standard dependencies beyond pandas).

---

### 2. Functional Scope

```
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
  5. Near-Duplicate Analysis (Normalized Edit Distance)                  │
  6. Descriptive Summary Statistics                                      ▼
               │                                              [ Read-Only Terminal Report ]
               ▼
  7. Interactive Q&A Cleaning & Remediation
               │
               ▼
  8. Export (CSV / JSON Conversion)
```

---

### 3. Specifications

#### Stage 1: File Ingestion & Parsing Error Diagnostics (Part A.1, A.2, C)
*   **Input Flexibility:** Detects file extension (`.csv`, `.tsv`, `.txt`, `.json`, `.jsonl`).
*   **CSV Parsing Diagnostics:**
    *   Pre-scans the raw text with Python’s `csv.Sniffer` to infer delimiter, quote characters, and line terminators.
    *   Catches parsing errors by reading raw byte streams to identify line numbers with mismatched field counts or invalid quote escaping before passing to `pandas.read_csv()`.
*   **JSON Parsing Diagnostics:**
    *   Supports standard JSON records/arrays as well as Line-Delimited JSON (JSONL).
    *   Tracks and reports specific JSON decode errors, capturing the exact line number and byte offset of malformed syntax.

#### Stage 2: Schema Health & Mixed Data Type Detection (Part A.3)
*   **Mixed Data Type Identification:**
    *   Iterates through columns stored as generic `object` dtypes.
    *   Inspects the Python `type()` of every non-null element in each column (e.g., detecting rows containing `int` mixed with `str` or `dict`).
    *   Reports the distribution of underlying types per column (e.g., `Column 'customer_id': 95% int, 5% str`).
*   **Summary Statistics (`.describe()` Extension):**
    *   Generates separate or unified summaries for numeric, datetime, and categorical columns.
    *   Adds metrics: total null count, null percentage, whitespace-only cell count, zero-value count, and distinct value count.

#### Stage 3: Exact Duplicate Row Detection (Part A.4)
*   **Hash-Based Row Comparison:**
    *   Serializes each row to a deterministic string representation and computes a cryptographic SHA-256 hash (or fast deterministic pandas object hash via `pandas.util.hash_pandas_object`).
    *   Groups rows sharing identical hash values.
    *   Outputs the total count of duplicate rows, the number of distinct duplicate clusters, and previews of the affected row indices.

#### Stage 4: Near-Duplicate Row Identification (Part A.5)
*   **Text Normalization:**
    *   Transforms selected or all string/text columns: converts to lowercase, strips leading/trailing whitespace, and strips all non-alphanumeric characters.
*   **Fuzzy Comparison:**
    *   Utilizes normalized string concatenation per row.
    *   Compares candidate rows using Levenshtein distance / `difflib.SequenceMatcher.ratio()`
        against a user-configurable similarity threshold (e.g., similarity $[backslash]ge 0.85$).
    *   Implements blocking/bucketing (e.g., grouping by row length or token prefix) to prevent $O(N^2)$ exponential slowdowns on larger datasets.
    *   Reports candidate near-duplicate pairs with similarity scores and field-level diffs.

#### Stage 5: Train/Test Set Cross-File Verification (Part B)
*   **Strict Read-Only Mode:** Operates without modifying either input file.
*   **Verifications Performed:**
    1.  **Schema Alignment:** Identifies columns present in the training set but missing in the test set, and vice versa.
    2.  **Data Contamination / Leakage:** Hashes all rows in both datasets to detect identical samples appearing across both train and test partitions.
    3.  **Novel Categorical Values:** Identifies categorical feature values present in the test set that never appeared in the training set (which causes out-of-vocabulary errors during model inference).
    4.  **Distribution Shift Alert:** Flags basic statistical divergence in numerical column means and standard deviations between splits.

#### Stage 6: Interactive Terminal Q&A Cleaning & Export (Part A.6, Part C)
*   **Step-by-Step Prompt Workflow:**
    *   **Question 1 (Exact Duplicates):** Keep first occurrence, keep last occurrence, drop all occurrences, or retain all?
    *   **Question 2 (Near-Duplicates):** Inspect flagged near-duplicate pairs interactively and choose whether to merge, drop specific indices, or ignore.
    *   **Question 3 (Mixed Data Types):** For each column with mixed types, offer options to:
        - Coerce to numeric (converting invalid values to `NaN`).
        - Coerce to string representation.
        - Drop rows containing incompatible types.
    *   **Question 4 (Missing Values):** Options to drop columns exceeding a null threshold, or drop rows exceeding a null threshold.
    *   **Question 5 (Output File Configuration):**
        - Select target format (`CSV` or `JSON`).
        - If CSV: select delimiter (comma, tab, pipe, semicolon).
        - If JSON: select orientation (`records`, `split`, `index`, or `jsonl`).
        - Enter destination file path.

---

### 4. Function Catalog

| Function Name | Primary Purpose |
| :--- | :--- |
| `read_source_dataset_file(...)` | Ingests CSV/JSON, sniffs metadata, reports raw parsing anomalies. |
| `detect_malformed_csv_rows(...)` | Pre-parses raw line streams to catch row-level delimiter mismatches. |
| `evaluate_column_data_types(...)` | Identifies mixed Python object types residing within single columns. |
| `generate_comprehensive_descriptive_statistics(...)` | Builds enriched `.describe()` tables with null and whitespace metrics. |
| `identify_exact_duplicate_rows(...)` | Hashes row contents to locate and group identical row records. |
| `identify_near_duplicate_rows(...)` | Normalizes text and calculates Levenshtein/similarity metrics across rows. |
| `execute_train_test_split_integrity_check(...)` | Evaluates feature overlap, leakage, and category shifts between 2 files. |
| `prompt_interactive_cleaning_configuration(...)` | Prompts user through terminal Q&A to configure cleaning decisions. |
| `apply_dataset_cleaning_transformations(...)` | Executes selected cleaning transformations on the DataFrame. |
| `export_processed_dataset_file(...)` | Serializes and writes DataFrame to CSV or JSON with validation. |
| `main_execution_controller(...)` | CLI entry point orchestrating single-file or train/test verification workflows. |

"""

"""
# Python Rules:

- always extensive doc strings
- NEVER remove (non-deprecated) docs from a doc string!!!! (e.g. when making a new version of a function)
- always comments
- always extremely clear unique names
- never unsafe code
- always try-except with traceback
- always error handling
- always clear specific meaningful helpful error messages (no error hiding)
- always production safe code
- clarity is a goal
- communication is the goal
- brevity is not a goal
- aesthetics are not a goal
- modular functional, not OOP (where possible)
- no hard coding of environment variables
- flat-file (unless project specifically requires otherwise)

"""

import argparse
import concurrent.futures  # RESTORED: process-pool parallelism for duplicate scanning
import csv
import json
import os
import re
import sys
import traceback
from collections import defaultdict
from collections.abc import Callable  # Used for typed callback / backend dispatch signatures
from typing import Any

import numpy as np  # Used for chunked hash concatenation in parallel exact-duplicate mode
import pandas as pd

# =====================================================================
# SECTION 1: INGESTION AND LOW-LEVEL PARSING DIAGNOSTICS
# =====================================================================


def detect_file_format_type(source_file_path: str) -> str:
    """
    Identifies the format category of a given file path based on its extension.

    Parameters:
        source_file_path (str): The absolute or relative path to the file.

    Returns:
        str: Detected file format identifier ('csv', 'tsv', 'json', 'jsonl', or 'unknown').

    Raises:
        FileNotFoundError: If the specified file does not exist on disk.
    """
    if not os.path.exists(source_file_path):
        error_message: str = f"The specified source file path does not exist: '{source_file_path}'"
        raise FileNotFoundError(error_message)

    file_extension_normalized: str = os.path.splitext(source_file_path)[1].lower()

    if file_extension_normalized in [".csv", ".txt"]:
        return "csv"
    if file_extension_normalized == ".tsv":
        return "tsv"
    if file_extension_normalized == ".json":
        return "json"
    if file_extension_normalized in [".jsonl", ".ndjson"]:
        return "jsonl"

    return "unknown"


def detect_malformed_csv_rows(
    source_file_path: str,
    delimiter_character: str = ",",
    maximum_line_scan_limit: int | None = None,
) -> list[dict[str, int]]:
    """
    Performs streaming line-by-line validation to detect rows with mismatched
    token counts compared to the header schema.

    Parameters:
        source_file_path (str): Path to the delimited text file.
        delimiter_character (str): Delimiter character dividing column tokens.
        maximum_line_scan_limit (int | None): Maximum lines to scan, or None for entire file.

    Returns:
        list[dict[str, int]]: List of records describing malformed lines.
    """
    malformed_row_records: list[dict[str, int]] = []

    try:
        with open(source_file_path, mode="r", encoding="utf-8", errors="replace") as file_stream:
            csv_reader_instance = csv.reader(file_stream, delimiter=delimiter_character)

            header_row: list[str] = next(csv_reader_instance, [])
            expected_field_count: int = len(header_row)

            if expected_field_count == 0:
                return malformed_row_records

            current_line_number: int = 1

            for row_tokens in csv_reader_instance:
                current_line_number += 1

                if maximum_line_scan_limit and current_line_number > maximum_line_scan_limit:
                    break

                if not row_tokens:
                    continue

                observed_field_count: int = len(row_tokens)
                if observed_field_count != expected_field_count:
                    malformed_row_records.append(
                        {
                            "line_number": current_line_number,
                            "expected_field_count": expected_field_count,
                            "observed_field_count": observed_field_count,
                        }
                    )

        return malformed_row_records

    except Exception:
        sys.stderr.write(
            f"[ERROR] An unexpected error occurred during low-level CSV row scanning.\n"
            f"File: {source_file_path}\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        return malformed_row_records


def read_source_dataset_file(
    source_file_path: str,
    user_specified_delimiter: str | None = None,
) -> tuple[pd.DataFrame, list[dict[str, int]]]:
    """
    Reads a CSV, TSV, JSON, or JSONL file directly into a pandas DataFrame
    using standard format-native parsing.

    Parameters:
        source_file_path (str): File system path to the input dataset.
        user_specified_delimiter (str | None): Optional explicit delimiter override.

    Returns:
        tuple[pd.DataFrame, list[dict[str, int]]]:
            1. Loaded pandas DataFrame.
            2. List of malformed row diagnostic dictionaries.

    Raises:
        ValueError: If the file format is unsupported or parsing fails entirely.
    """
    detected_format: str = detect_file_format_type(source_file_path)
    malformed_rows: list[dict[str, int]] = []

    try:
        if detected_format in ["csv", "tsv"]:
            # Standard extension-based delimiter default
            if user_specified_delimiter is not None:
                effective_delimiter: str = user_specified_delimiter
            elif detected_format == "tsv":
                effective_delimiter = "\t"
            else:
                effective_delimiter = ","

            # Check for low-level line length mismatches
            malformed_rows = detect_malformed_csv_rows(
                source_file_path=source_file_path,
                delimiter_character=effective_delimiter,
            )

            # Direct pandas CSV read
            loaded_dataframe: pd.DataFrame = pd.read_csv(
                source_file_path,
                sep=effective_delimiter,
                on_bad_lines="skip",
                encoding="utf-8",
                encoding_errors="replace",
            )
            return loaded_dataframe, malformed_rows

        elif detected_format in ["json", "jsonl"]:
            is_line_delimited: bool = detected_format == "jsonl"

            try:
                loaded_dataframe = pd.read_json(
                    source_file_path,
                    lines=is_line_delimited,
                    encoding="utf-8",
                )
                return loaded_dataframe, malformed_rows
            except Exception:
                parsed_json_records: list[dict[str, Any]] = []
                with open(source_file_path, mode="r", encoding="utf-8", errors="replace") as json_stream:
                    for line_index, raw_line_text in enumerate(json_stream, start=1):
                        stripped_line: str = raw_line_text.strip()
                        if not stripped_line:
                            continue
                        try:
                            record_data: Any = json.loads(stripped_line)
                            if isinstance(record_data, dict):
                                parsed_json_records.append(record_data)
                            elif isinstance(record_data, list):
                                for sub_record in record_data:
                                    if isinstance(sub_record, dict):
                                        parsed_json_records.append(sub_record)
                        except json.JSONDecodeError:
                            malformed_rows.append(
                                {
                                    "line_number": line_index,
                                    "expected_field_count": 0,
                                    "observed_field_count": 0,
                                }
                            )

                loaded_dataframe = pd.DataFrame(parsed_json_records)
                return loaded_dataframe, malformed_rows

        else:
            raise ValueError(
                f"Unsupported file format for path '{source_file_path}'. "
                f"Expected .csv, .tsv, .txt, .json, or .jsonl extension."
            )

    except Exception:
        sys.stderr.write(
            f"[FATAL ERROR] Ingestion failed for source dataset: {source_file_path}\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        raise

# =====================================================================
# SECTION 2: COLUMN HEALTH & MIXED DATA TYPE DIAGNOSTICS
# =====================================================================


def detect_mixed_data_types_in_dataframe(
    source_dataframe: pd.DataFrame,
) -> dict[str, dict[str, int]]:
    """
    Analyzes object and mixed-type columns to identify instances where
    multiple distinct underlying Python types coexist within the same column.

    Parameters:
        source_dataframe (pd.DataFrame): The DataFrame to analyze.

    Returns:
        dict[str, dict[str, int]]: Mapping of column names to frequency dictionaries
            of detected Python types. Columns with uniform types are omitted.
    """
    mixed_type_columns_report: dict[str, dict[str, int]] = {}

    for column_name in source_dataframe.columns:
        column_series: pd.Series = source_dataframe[column_name]

        # Inspect non-null elements
        non_null_series: pd.Series = column_series.dropna()
        if non_null_series.empty:
            continue

        # Extract type names for all non-null values
        type_name_counts: pd.Series = non_null_series.map(lambda value: type(value).__name__).value_counts()

        # A mixed-type condition occurs when more than one distinct type is present
        if len(type_name_counts) > 1:
            mixed_type_columns_report[str(column_name)] = type_name_counts.to_dict()

    return mixed_type_columns_report


def generate_comprehensive_descriptive_statistics(
    source_dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    """
    Computes standard pandas describe statistics alongside extended column-level
    data quality metrics (null counts, null percentages, whitespace counts, unique values).

    Parameters:
        source_dataframe (pd.DataFrame): The DataFrame to evaluate.

    Returns:
        tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
            1. Standard pandas .describe(include='all') DataFrame.
            2. Dictionary mapping column names to calculated extended metrics.
    """
    total_row_count: int = len(source_dataframe)
    extended_column_metrics: dict[str, dict[str, Any]] = {}

    # Calculate standard describe
    try:
        standard_describe_dataframe: pd.DataFrame = source_dataframe.describe(include="all").fillna("")
    except Exception:
        standard_describe_dataframe = pd.DataFrame()

    for column_name in source_dataframe.columns:
        column_series: pd.Series = source_dataframe[column_name]

        missing_value_count: int = int(column_series.isna().sum())
        missing_value_percentage: float = (
            (missing_value_count / total_row_count * 100.0) if total_row_count > 0 else 0.0
        )
        unique_value_count: int = int(column_series.nunique(dropna=False))

        # Check for whitespace-only strings
        whitespace_only_cell_count: int = 0
        if column_series.dtype == "object":
            whitespace_only_cell_count = int(
                column_series.dropna()
                .map(lambda cell_value: 1 if isinstance(cell_value, str) and cell_value.strip() == "" else 0)
                .sum()
            )

        extended_column_metrics[str(column_name)] = {
            "total_rows": total_row_count,
            "missing_value_count": missing_value_count,
            "missing_value_percentage": round(missing_value_percentage, 2),
            "whitespace_only_cell_count": whitespace_only_cell_count,
            "unique_value_count": unique_value_count,
            "pandas_dtype": str(column_series.dtype),
        }

    return standard_describe_dataframe, extended_column_metrics


# =====================================================================
# SECTION 3: EXACT DUPLICATE DETECTION (HASH-BASED)
# =====================================================================

# =====================================================================
# PARALLEL EXECUTION CONFIGURATION (SECTIONS 3 AND 4)
# =====================================================================

# Minimum unique normalized strings before near-duplicate scanning switches
# from sequential to multi-process mode. Below this, process startup and
# metadata pickling cost more than the scan itself.
PARALLEL_NEAR_DUPLICATE_MINIMUM_CANDIDATE_COUNT: int = 5_000

# Minimum row count before exact-duplicate hashing switches to chunked
# multi-process hashing. pandas.util.hash_pandas_object is already
# vectorized C, so parallelism only pays off on very large frames where
# per-chunk pickling cost is amortized.
PARALLEL_EXACT_DUPLICATE_MINIMUM_ROW_COUNT: int = 1_000_000


def resolve_worker_process_count(requested_worker_process_count: int | None) -> int:
    """
    Resolves the number of worker processes to use for parallel duplicate scanning.

    Parameters:
        requested_worker_process_count (int | None): Explicit user-requested worker
            count, or None to auto-detect from available CPU cores.

    Returns:
        int: A worker count of at least 1. Auto-detection reserves one core for
            the main process so the terminal remains responsive during long scans.
    """
    if requested_worker_process_count is not None and requested_worker_process_count >= 1:
        return requested_worker_process_count

    detected_cpu_core_count: int | None = os.cpu_count()
    # os.cpu_count() can legitimately return None on exotic platforms; fall back to 2.
    return max(1, (detected_cpu_core_count or 2) - 1)


# ---------------------------------------------------------------------
# Worker-process module-level state for near-duplicate scanning.
# These globals exist ONLY inside spawned worker processes. They are
# populated exactly once per worker by the pool initializer, so the
# (potentially large) candidate metadata table is pickled once per
# worker instead of once per submitted task chunk.
# ---------------------------------------------------------------------
_NEAR_DUPLICATE_WORKER_SORTED_CANDIDATE_METADATA: list[tuple[int, str, int, tuple[int, ...]]] = []
_NEAR_DUPLICATE_WORKER_SIMILARITY_THRESHOLD: float = 0.98
_NEAR_DUPLICATE_WORKER_MAXIMUM_ALLOWABLE_EDIT_DISTANCE: int = 2


def _initialize_near_duplicate_worker_process(
    sorted_candidate_metadata: list[tuple[int, str, int, tuple[int, ...]]],
    similarity_threshold: float,
    maximum_allowable_edit_distance: int,
) -> None:
    """
    ProcessPoolExecutor initializer. Installs the shared candidate metadata table
    and scan parameters into this worker process's module globals.

    Parameters:
        sorted_candidate_metadata (list[tuple[int, str, int, tuple[int, ...]]]):
            The full length-sorted candidate table built by the main process.
        similarity_threshold (float): Minimum normalized similarity ratio [0.0 - 1.0].
        maximum_allowable_edit_distance (int): Maximum absolute character edits allowed.
    """
    global _NEAR_DUPLICATE_WORKER_SORTED_CANDIDATE_METADATA
    global _NEAR_DUPLICATE_WORKER_SIMILARITY_THRESHOLD
    global _NEAR_DUPLICATE_WORKER_MAXIMUM_ALLOWABLE_EDIT_DISTANCE

    _NEAR_DUPLICATE_WORKER_SORTED_CANDIDATE_METADATA = sorted_candidate_metadata
    _NEAR_DUPLICATE_WORKER_SIMILARITY_THRESHOLD = similarity_threshold
    _NEAR_DUPLICATE_WORKER_MAXIMUM_ALLOWABLE_EDIT_DISTANCE = maximum_allowable_edit_distance


def _scan_near_duplicate_chunk_in_worker(
    outer_position_range: tuple[int, int],
) -> tuple[list[tuple[int, int, int, int]], int]:
    """
    Worker-process task entry point. Scans one contiguous chunk of outer positions
    against the worker-global candidate metadata table.

    Parameters:
        outer_position_range (tuple[int, int]): (inclusive_start, exclusive_end)
            outer-loop position range assigned to this task.

    Returns:
        tuple[list[tuple[int, int, int, int]], int]:
            1. Matched pair tuples (outer_position, inner_position, edit_distance, maximum_length).
            2. Number of Levenshtein distance computations performed in this chunk.
    """
    return scan_candidate_position_range_for_near_duplicate_pairs(
        sorted_candidate_metadata=_NEAR_DUPLICATE_WORKER_SORTED_CANDIDATE_METADATA,
        outer_position_range_start=outer_position_range[0],
        outer_position_range_end=outer_position_range[1],
        similarity_threshold=_NEAR_DUPLICATE_WORKER_SIMILARITY_THRESHOLD,
        maximum_allowable_edit_distance=_NEAR_DUPLICATE_WORKER_MAXIMUM_ALLOWABLE_EDIT_DISTANCE,
        maximum_candidate_comparisons=None,
        progress_report_callback=None,
    )


def scan_candidate_position_range_for_near_duplicate_pairs(
    sorted_candidate_metadata: list[tuple[int, str, int, tuple[int, ...]]],
    outer_position_range_start: int,
    outer_position_range_end: int,
    similarity_threshold: float,
    maximum_allowable_edit_distance: int,
    maximum_candidate_comparisons: int | None = None,
    progress_report_callback: Callable[[int, int, int], None] | None = None,
) -> tuple[list[tuple[int, int, int, int]], int]:
    """
    Scans a contiguous range of outer positions within the length-sorted candidate
    metadata table and returns every near-duplicate pair whose OUTER member falls
    inside the range. The inner loop always runs over the full remainder of the
    table (outer_position + 1 onward), so partitioning the outer range across
    processes covers every unordered pair exactly once with zero overlap.

    This function is deliberately free of pandas / DataFrame access and free of
    console side effects (other than the optional injected callback) so that it
    executes identically in the main process (sequential mode) and inside
    ProcessPoolExecutor worker processes (parallel mode).

    Pre-filters applied per candidate pair (identical to the original inline scan):
      1. Length-window break: the table is length-sorted, so once the length gap
         exceeds the absolute edit ceiling, the inner loop terminates.
      2. Per-pair effective edit ceiling derived from both the proportional
         similarity threshold and the absolute edit cap.
      3. 36-slot character-histogram L1 lower bound (L1/2 <= edit distance).
      4. Banded / cutoff Levenshtein (rapidfuzz C++ backend when installed).

    Parameters:
        sorted_candidate_metadata (list[tuple[int, str, int, tuple[int, ...]]]):
            Entries of (normalized_length, normalized_text,
            dataframe_positional_index, character_histogram), sorted ascending
            by normalized_length.
        outer_position_range_start (int): Inclusive start of the outer-loop range.
        outer_position_range_end (int): Exclusive end of the outer-loop range.
        similarity_threshold (float): Minimum normalized similarity ratio [0.0 - 1.0].
        maximum_allowable_edit_distance (int): Maximum absolute character edits allowed.
        maximum_candidate_comparisons (int | None): Safety ceiling on distance
            computations within this range. None disables the ceiling.
        progress_report_callback (Callable[[int, int, int], None] | None): Optional
            callable invoked periodically with (outer_positions_scanned_in_range,
            distance_computations_performed, pairs_found_so_far).

    Returns:
        tuple[list[tuple[int, int, int, int]], int]:
            1. Matched pair tuples
               (outer_metadata_position, inner_metadata_position, edit_distance, maximum_length).
            2. Total Levenshtein distance computations performed in this range.
    """
    matched_pair_tuples: list[tuple[int, int, int, int]] = []
    total_distance_computations_performed: int = 0

    total_candidate_count: int = len(sorted_candidate_metadata)
    range_size: int = max(0, outer_position_range_end - outer_position_range_start)
    progress_reporting_chunk_size: int = max(1, range_size // 10)

    for outer_position in range(outer_position_range_start, outer_position_range_end):
        length_a, string_a, _dataframe_position_a, histogram_a = sorted_candidate_metadata[outer_position]

        # Periodic progress callback (sequential mode only; workers pass None).
        outer_positions_scanned_in_range: int = (outer_position - outer_position_range_start) + 1
        if progress_report_callback is not None and (
            outer_positions_scanned_in_range % progress_reporting_chunk_size == 0
            or outer_positions_scanned_in_range == range_size
        ):
            progress_report_callback(
                outer_positions_scanned_in_range,
                total_distance_computations_performed,
                len(matched_pair_tuples),
            )

        for inner_position in range(outer_position + 1, total_candidate_count):
            length_b, string_b, _dataframe_position_b, histogram_b = sorted_candidate_metadata[inner_position]

            # PRE-FILTER 1 (window bound): length-sorted list — once the length
            # gap exceeds the absolute edit ceiling, no later entry can match.
            if (length_b - length_a) > maximum_allowable_edit_distance:
                break

            # Per-pair effective ceiling from both threshold and absolute cap.
            maximum_length: int = length_b  # length_b >= length_a by sort order
            ratio_based_edit_allowance: int = int(maximum_length * (1.0 - similarity_threshold))
            effective_maximum_edits: int = min(ratio_based_edit_allowance, maximum_allowable_edit_distance)
            if effective_maximum_edits == 0:
                continue
            if (length_b - length_a) > effective_maximum_edits:
                continue

            # PRE-FILTER 2 (histogram lower bound): 36 integer subtractions.
            histogram_l1_distance: int = 0
            histogram_bound_exceeded: bool = False
            l1_rejection_threshold: int = 2 * effective_maximum_edits
            for slot_index in range(36):
                histogram_l1_distance += abs(histogram_a[slot_index] - histogram_b[slot_index])
                if histogram_l1_distance > l1_rejection_threshold:
                    histogram_bound_exceeded = True
                    break
            if histogram_bound_exceeded:
                continue

            # FULL CHECK: banded/cutoff Levenshtein, with optional budget ceiling.
            total_distance_computations_performed += 1
            if (
                maximum_candidate_comparisons is not None
                and total_distance_computations_performed > maximum_candidate_comparisons
            ):
                return matched_pair_tuples, total_distance_computations_performed

            edit_distance: int = compute_edit_distance_with_cutoff(
                string_a, string_b, effective_maximum_edits
            )
            if edit_distance > effective_maximum_edits:
                continue

            matched_pair_tuples.append(
                (outer_position, inner_position, edit_distance, maximum_length)
            )

    return matched_pair_tuples, total_distance_computations_performed


# def identify_exact_duplicate_rows(
#     source_dataframe: pd.DataFrame,
# ) -> dict[str, Any]:
#     """
#     Identifies completely identical rows across all columns using vectorized
#     64-bit integer hashing for scale and efficiency.

#     OPTIMIZED IMPLEMENTATION: Cluster construction is performed in a single
#     O(N) pass that buckets row labels by hash value. The previous version
#     re-scanned the entire hash column once per duplicate cluster
#     (O(clusters * N)), which became quadratic on files with many clusters.

#     Parameters:
#         source_dataframe (pd.DataFrame): The DataFrame to evaluate.

#     Returns:
#         dict[str, Any]: Diagnostic report containing:
#             - 'total_duplicate_rows_count': int
#             - 'duplicate_cluster_count': int
#             - 'duplicate_index_clusters': list[list[int]] (grouped duplicate row indices)
#     """
#     if source_dataframe.empty:
#         return {
#             "total_duplicate_rows_count": 0,
#             "duplicate_cluster_count": 0,
#             "duplicate_index_clusters": [],
#         }

#     try:
#         # Generate 64-bit deterministic hash array across all columns.
#         row_hashes_series: pd.Series = pd.util.hash_pandas_object(source_dataframe, index=False)

#         # Single vectorized pass: mark every row whose hash appears more than
#         # once anywhere in the file (keep=False marks ALL members of each
#         # duplicate group, not just the repeats).
#         duplicated_row_mask = row_hashes_series.duplicated(keep=False).to_numpy()

#         # Extract only the duplicated rows' labels and hash values as flat
#         # numpy arrays (no per-cluster rescanning of the full column).
#         duplicated_row_labels = source_dataframe.index.to_numpy()[duplicated_row_mask]
#         duplicated_hash_values = row_hashes_series.to_numpy()[duplicated_row_mask]

#         # Bucket row labels by shared hash value in one linear walk.
#         cluster_labels_by_hash: dict[int, list[Any]] = defaultdict(list)
#         for hash_value, row_label in zip(duplicated_hash_values, duplicated_row_labels):
#             cluster_labels_by_hash[hash_value].append(row_label)

#         duplicate_index_clusters: list[list[Any]] = [
#             list(cluster_labels) for cluster_labels in cluster_labels_by_hash.values()
#         ]
#         total_duplicate_rows_count: int = sum(
#             len(cluster_labels) for cluster_labels in duplicate_index_clusters
#         )

#         return {
#             "total_duplicate_rows_count": total_duplicate_rows_count,
#             "duplicate_cluster_count": len(duplicate_index_clusters),
#             "duplicate_index_clusters": duplicate_index_clusters,
#         }

#     except Exception:
#         sys.stderr.write(
#             f"[ERROR] An unexpected failure occurred during exact duplicate hashing.\n"
#             f"Traceback:\n{traceback.format_exc()}\n"
#         )
#         return {
#             "total_duplicate_rows_count": 0,
#             "duplicate_cluster_count": 0,
#             "duplicate_index_clusters": [],
#         }

def _hash_dataframe_row_chunk_for_duplicate_detection(
    dataframe_row_chunk: pd.DataFrame,
) -> "np.ndarray[Any, np.dtype[np.uint64]]":
    """
    Worker-process task: computes deterministic 64-bit row hashes for one
    contiguous row-chunk of the source DataFrame.

    CORRECTNESS NOTE: pandas.util.hash_pandas_object with index=False hashes
    each row independently of every other row (per-column hashing combined
    row-wise, with a fixed default hash key). Therefore hashing row-chunks in
    separate processes and concatenating the results is bit-identical to
    hashing the whole frame in one pass.

    Parameters:
        dataframe_row_chunk (pd.DataFrame): A contiguous positional row slice.

    Returns:
        np.ndarray: uint64 hash values, one per row of the chunk, in row order.
    """
    return pd.util.hash_pandas_object(dataframe_row_chunk, index=False).to_numpy()


def identify_exact_duplicate_rows(
    source_dataframe: pd.DataFrame,
    worker_process_count: int | None = None,
) -> dict[str, Any]:
    """
    Identifies completely identical rows across all columns using vectorized
    64-bit integer hashing for scale and efficiency.

    OPTIMIZED IMPLEMENTATION: Cluster construction is performed in a single
    O(N) pass that buckets row labels by hash value. The previous version
    re-scanned the entire hash column once per duplicate cluster
    (O(clusters * N)), which became quadratic on files with many clusters.

    PARALLEL EXECUTION (multi-process hashing):
      When the row count reaches PARALLEL_EXACT_DUPLICATE_MINIMUM_ROW_COUNT
      and more than one worker is available, the frame is split into
      contiguous row-chunks that are hashed concurrently in a
      ProcessPoolExecutor and concatenated in original row order. Because
      hash_pandas_object(index=False) hashes rows independently with a fixed
      hash key, chunked results are bit-identical to a single-pass hash.
      Any pool failure falls back to the vectorized single-pass hash with a
      warning — results are never silently lost.

    Parameters:
        source_dataframe (pd.DataFrame): The DataFrame to evaluate.
        worker_process_count (int | None): Number of parallel worker processes
            for chunked hashing. None auto-detects (CPU cores minus one,
            minimum 1). A value of 1 forces single-pass hashing.

    Returns:
        dict[str, Any]: Diagnostic report containing:
            - 'total_duplicate_rows_count': int
            - 'duplicate_cluster_count': int
            - 'duplicate_index_clusters': list[list[int]] (grouped duplicate row indices)
    """
    if source_dataframe.empty:
        return {
            "total_duplicate_rows_count": 0,
            "duplicate_cluster_count": 0,
            "duplicate_index_clusters": [],
        }

    try:
        total_row_count: int = len(source_dataframe)
        resolved_worker_process_count: int = resolve_worker_process_count(worker_process_count)

        parallel_hashing_enabled: bool = (
            total_row_count >= PARALLEL_EXACT_DUPLICATE_MINIMUM_ROW_COUNT
            and resolved_worker_process_count > 1
        )

        row_hash_values_array: np.ndarray[Any, np.dtype[np.uint64]]

        if parallel_hashing_enabled:
            try:
                # Contiguous positional slices, one per worker; iloc slicing is
                # a view-cheap operation and preserves original row order.
                chunk_row_count: int = -(-total_row_count // resolved_worker_process_count)  # ceil div
                dataframe_row_chunks: list[pd.DataFrame] = [
                    source_dataframe.iloc[chunk_start : chunk_start + chunk_row_count]
                    for chunk_start in range(0, total_row_count, chunk_row_count)
                ]
                print(
                    f"  [STATUS] Exact-duplicate hashing: PARALLEL mode "
                    f"({len(dataframe_row_chunks)} chunks across "
                    f"{resolved_worker_process_count} worker processes).",
                    flush=True,
                )
                with concurrent.futures.ProcessPoolExecutor(
                    max_workers=resolved_worker_process_count
                ) as process_pool_executor:
                    # executor.map preserves input order, so concatenation
                    # reconstructs the exact original row order.
                    chunk_hash_arrays: list[np.ndarray[Any, np.dtype[np.uint64]]] = list(
                        process_pool_executor.map(
                            _hash_dataframe_row_chunk_for_duplicate_detection,
                            dataframe_row_chunks,
                        )
                    )
                row_hash_values_array = np.concatenate(chunk_hash_arrays)
            except Exception:
                sys.stderr.write(
                    f"[WARNING] Parallel exact-duplicate hashing failed; falling back to "
                    f"single-pass vectorized hashing. Root cause:\n{traceback.format_exc()}\n"
                )
                row_hash_values_array = pd.util.hash_pandas_object(
                    source_dataframe, index=False
                ).to_numpy()
        else:
            # Generate 64-bit deterministic hash array across all columns
            # in one vectorized pass (fastest path for small/medium frames).
            row_hash_values_array = pd.util.hash_pandas_object(
                source_dataframe, index=False
            ).to_numpy()

        # Single vectorized pass: mark every row whose hash appears more than
        # once anywhere in the file (keep=False marks ALL members of each
        # duplicate group, not just the repeats).
        row_hashes_series: pd.Series[int] = pd.Series(row_hash_values_array)
        duplicated_row_mask = row_hashes_series.duplicated(keep=False).to_numpy()

        # Extract only the duplicated rows' labels and hash values as flat
        # numpy arrays (no per-cluster rescanning of the full column).
        duplicated_row_labels = source_dataframe.index.to_numpy()[duplicated_row_mask]
        duplicated_hash_values = row_hash_values_array[duplicated_row_mask]

        # Bucket row labels by shared hash value in one linear walk.
        # strict=True guarantees the two arrays are the same length (they are
        # both filtered by the same mask; this assertion is defensive).
        cluster_labels_by_hash: dict[int, list[Any]] = defaultdict(list)
        for hash_value, row_label in zip(duplicated_hash_values, duplicated_row_labels, strict=True):
            cluster_labels_by_hash[int(hash_value)].append(row_label)

        duplicate_index_clusters: list[list[Any]] = [
            list(cluster_labels) for cluster_labels in cluster_labels_by_hash.values()
        ]
        total_duplicate_rows_count: int = sum(
            len(cluster_labels) for cluster_labels in duplicate_index_clusters
        )

        return {
            "total_duplicate_rows_count": total_duplicate_rows_count,
            "duplicate_cluster_count": len(duplicate_index_clusters),
            "duplicate_index_clusters": duplicate_index_clusters,
        }

    except Exception:
        sys.stderr.write(
            f"[ERROR] An unexpected failure occurred during exact duplicate hashing.\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        return {
            "total_duplicate_rows_count": 0,
            "duplicate_cluster_count": 0,
            "duplicate_index_clusters": [],
        }

# =====================================================================
# SECTION 4: EXACT LEVENSHTEIN DISTANCE ON TARGET TEXT COLUMNS
# =====================================================================


def detect_candidate_text_columns(source_dataframe: pd.DataFrame) -> list[str]:
    """
    Identifies high-cardinality string/object columns that represent free-form
    text content (excluding low-cardinality category labels, boolean flags, or IDs).

    Parameters:
        source_dataframe (pd.DataFrame): The DataFrame to evaluate.

    Returns:
        list[str]: Names of columns inferred to be free-form text.
    """
    candidate_text_columns: list[str] = []
    total_row_count: int = len(source_dataframe)

    for column_name in source_dataframe.columns:
        column_series: pd.Series = source_dataframe[column_name].dropna()
        if column_series.empty:
            continue

        if column_series.dtype == "object":
            unique_count: int = int(column_series.nunique())
            sample_non_nulls: list[str] = [str(val) for val in column_series.iloc[:100]]
            average_character_length: float = (
                sum(len(text) for text in sample_non_nulls) / len(sample_non_nulls)
                if sample_non_nulls
                else 0.0
            )

            # High cardinality (>5% of rows or >50 unique values) with substantial average length
            if (unique_count > 50 or (unique_count / total_row_count) > 0.05) and average_character_length >= 15.0:
                candidate_text_columns.append(str(column_name))

    # Fallback to all object columns if no high-length column was isolated
    if not candidate_text_columns:
        candidate_text_columns = [
            str(col) for col in source_dataframe.columns if source_dataframe[col].dtype == "object"
        ]

    return candidate_text_columns


def normalize_text_content_alphanumeric_lowercase(raw_text_value: Any) -> str:
    """
    Lowercases a text string and removes all non-alphanumeric characters.

    Parameters:
        raw_text_value (Any): The raw cell content.

    Returns:
        str: Alphanumeric lowercase string containing only [a-z0-9].
    """
    if raw_text_value is None or pd.isna(raw_text_value):
        return ""
    return re.sub(r"[^a-z0-9]", "", str(raw_text_value).lower())


def calculate_exact_levenshtein_distance(
    first_string: str,
    second_string: str,
    maximum_distance_cutoff: int | None = None,
) -> int:
    """
    Computes the exact Levenshtein edit distance (minimum single-character
    insertions, deletions, or substitutions required to transform first_string
    into second_string) using the two-row Wagner-Fischer dynamic programming algorithm.

    Parameters:
        first_string (str): The initial normalized character string.
        second_string (str): The target normalized character string.
        maximum_distance_cutoff (int | None): Optional ceiling. If the distance is
            guaranteed to exceed this cutoff, computation terminates early.

    Returns:
        int: The exact integer Levenshtein edit distance.
    """
    if first_string == second_string:
        return 0

    length_first: int = len(first_string)
    length_second: int = len(second_string)

    if length_first == 0:
        return length_second
    if length_second == 0:
        return length_first

    # Ensure first_string is the shorter sequence to minimize memory allocation
    if length_first > length_second:
        first_string, second_string = second_string, first_string
        length_first, length_second = length_second, length_first

    # If the length difference alone exceeds the cutoff, exit immediately
    if maximum_distance_cutoff is not None:
        if (length_second - length_first) > maximum_distance_cutoff:
            return maximum_distance_cutoff + 1

    previous_row_distances: list[int] = list(range(length_first + 1))
    current_row_distances: list[int] = [0] * (length_first + 1)

    for index_second, character_second in enumerate(second_string, start=1):
        current_row_distances[0] = index_second
        row_minimum_distance: int = current_row_distances[0]

        for index_first, character_first in enumerate(first_string, start=1):
            substitution_cost: int = 0 if character_first == character_second else 1

            current_row_distances[index_first] = min(
                previous_row_distances[index_first] + 1,
                current_row_distances[index_first - 1] + 1,
                previous_row_distances[index_first - 1] + substitution_cost,
            )

            if current_row_distances[index_first] < row_minimum_distance:
                row_minimum_distance = current_row_distances[index_first]

        # Early termination check
        if maximum_distance_cutoff is not None and row_minimum_distance > maximum_distance_cutoff:
            return maximum_distance_cutoff + 1

        previous_row_distances = current_row_distances[:]

    return previous_row_distances[length_first]


# =====================================================================
# OPTIONAL ACCELERATION: rapidfuzz (C++ Levenshtein with cutoff).
# Pure-python fallback is used automatically if not installed.
# Install with:  pip install rapidfuzz
# =====================================================================
# Holds the rapidfuzz Levenshtein distance callable when the package is
# installed, otherwise None. Typing this as an optional Callable lets the
# type checker verify the None-guard in the dispatcher below.
_rapidfuzz_levenshtein_distance_function: Callable[..., int] | None
try:
    from rapidfuzz.distance import Levenshtein as _rapidfuzz_levenshtein_namespace

    _rapidfuzz_levenshtein_distance_function = _rapidfuzz_levenshtein_namespace.distance
    RAPIDFUZZ_ACCELERATION_AVAILABLE: bool = True
except ImportError:
    _rapidfuzz_levenshtein_distance_function = None
    RAPIDFUZZ_ACCELERATION_AVAILABLE = False


# Fixed alphabet for the character-histogram pre-filter. Normalized text
# contains only [a-z0-9], so 36 buckets fully describe it.
_HISTOGRAM_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz0123456789"
_HISTOGRAM_CHAR_TO_SLOT: dict[str, int] = {
    character: slot_index for slot_index, character in enumerate(_HISTOGRAM_ALPHABET)
}


def build_character_frequency_histogram(normalized_text: str) -> tuple[int, ...]:
    """
    Builds a 36-slot character frequency histogram for a normalized
    [a-z0-9] string. Used as a constant-time lower-bound pre-filter:
    for any two strings, levenshtein(a, b) >= L1(hist_a, hist_b) / 2,
    because a substitution changes at most two histogram slots and an
    insertion/deletion changes exactly one.

    Parameters:
        normalized_text (str): Text already normalized to [a-z0-9].

    Returns:
        tuple[int, ...]: 36-element frequency tuple (a-z then 0-9).
    """
    slot_counts: list[int] = [0] * 36
    for character in normalized_text:
        slot_index: int | None = _HISTOGRAM_CHAR_TO_SLOT.get(character)
        if slot_index is not None:
            slot_counts[slot_index] += 1
    return tuple(slot_counts)


def calculate_banded_levenshtein_distance(
    first_string: str,
    second_string: str,
    maximum_distance_cutoff: int,
) -> int:
    """
    Computes Levenshtein distance restricted to a diagonal band of width
    (2 * cutoff + 1) — the Ukkonen banded optimization. Any true distance
    exceeding the cutoff is reported as (cutoff + 1); exact values are
    only needed at or below the cutoff, which is all the caller uses.

    Complexity: O(cutoff * max_length) time — for cutoff=2 this is ~250x
    fewer cell operations than the full O(len_a * len_b) matrix on
    typical 300-character text fields.

    Parameters:
        first_string (str): First normalized string.
        second_string (str): Second normalized string.
        maximum_distance_cutoff (int): Maximum edit distance of interest.

    Returns:
        int: Exact distance if <= cutoff, otherwise (cutoff + 1).
    """
    if first_string == second_string:
        return 0

    length_first: int = len(first_string)
    length_second: int = len(second_string)

    # Ensure first_string is the shorter sequence.
    if length_first > length_second:
        first_string, second_string = second_string, first_string
        length_first, length_second = length_second, length_first

    # Length difference alone already exceeds the cutoff -> no match possible.
    if (length_second - length_first) > maximum_distance_cutoff:
        return maximum_distance_cutoff + 1

    if length_first == 0:
        return length_second

    band_sentinel_value: int = maximum_distance_cutoff + 1

    # Row 0 holds true distances; values beyond the cutoff naturally act
    # as out-of-band sentinels (anything read from them stays > cutoff).
    previous_row_distances: list[int] = list(range(length_first + 1))
    current_row_distances: list[int] = [band_sentinel_value] * (length_first + 1)

    for index_second in range(1, length_second + 1):
        character_second: str = second_string[index_second - 1]

        # Only cells within |i - j| <= cutoff can hold values <= cutoff.
        band_low: int = max(1, index_second - maximum_distance_cutoff)
        band_high: int = min(length_first, index_second + maximum_distance_cutoff)

        # Seed the cell immediately left of the band (read as "insertion" source).
        current_row_distances[band_low - 1] = (
            index_second if band_low == 1 else band_sentinel_value
        )

        row_minimum_distance: int = band_sentinel_value

        for index_first in range(band_low, band_high + 1):
            substitution_cost: int = (
                0 if first_string[index_first - 1] == character_second else 1
            )
            best_cell_value: int = previous_row_distances[index_first - 1] + substitution_cost
            deletion_value: int = previous_row_distances[index_first] + 1
            if deletion_value < best_cell_value:
                best_cell_value = deletion_value
            insertion_value: int = current_row_distances[index_first - 1] + 1
            if insertion_value < best_cell_value:
                best_cell_value = insertion_value

            current_row_distances[index_first] = best_cell_value
            if best_cell_value < row_minimum_distance:
                row_minimum_distance = best_cell_value

        # Invalidate the cell just right of the band so the next iteration
        # never reads a stale value from two rows ago.
        if band_high + 1 <= length_first:
            current_row_distances[band_high + 1] = band_sentinel_value

        # Entire band exceeded the cutoff -> distance can only grow. Bail out.
        if row_minimum_distance > maximum_distance_cutoff:
            return maximum_distance_cutoff + 1

        # Swap row buffers (no per-iteration allocation).
        previous_row_distances, current_row_distances = (
            current_row_distances,
            previous_row_distances,
        )

    final_distance: int = previous_row_distances[length_first]
    return final_distance if final_distance <= maximum_distance_cutoff else band_sentinel_value


def compute_edit_distance_with_cutoff(
    first_string: str,
    second_string: str,
    maximum_distance_cutoff: int,
) -> int:
    """
    Dispatches edit-distance computation to the fastest available backend:
    rapidfuzz (C++, if installed) or the pure-Python banded implementation.

    Parameters:
        first_string (str): First normalized string.
        second_string (str): Second normalized string.
        maximum_distance_cutoff (int): Maximum edit distance of interest.

    Returns:
        int: Exact distance if <= cutoff, otherwise (cutoff + 1).
    """
    if _rapidfuzz_levenshtein_distance_function is not None:
            # rapidfuzz returns (score_cutoff + 1) when the cutoff is exceeded,
            # which matches the pure-Python contract exactly.
            return _rapidfuzz_levenshtein_distance_function(
                first_string, second_string, score_cutoff=maximum_distance_cutoff
            )
    return calculate_banded_levenshtein_distance(
            first_string, second_string, maximum_distance_cutoff
        )


# def identify_near_duplicate_rows(
#     source_dataframe: pd.DataFrame,
#     target_columns_subset: list[str] | None = None,
#     similarity_threshold: float = 0.98,
#     maximum_allowable_edit_distance: int = 2,
#     minimum_character_length: int = 15,
#     maximum_candidate_comparisons: int | None = None,
# ) -> list[dict[str, Any]]:
#     """
#     Identifies near-duplicate text records by evaluating exact Levenshtein edit
#     distance on designated free-form text column(s). Applies both a proportional
#     similarity threshold and an absolute edit distance ceiling.

#     OPTIMIZED IMPLEMENTATION (sorted-neighbor window strategy):
#       1. Text normalization is vectorized (single pandas pass, no iterrows).
#       2. Rows with byte-identical normalized text are collapsed to a single
#          representative (identical strings were already skipped by design —
#          they are the exact-duplicate stage's responsibility). NOTE: this means
#          if rows A and B normalize identically and row C is within threshold
#          of both, one pair (representative, C) is reported rather than two
#          redundant pairs — same information, fewer duplicate reports.
#       3. Unique strings are sorted by length. Because an edit distance of K
#          implies a length difference of at most K, each string is compared
#          only against a small sliding window of length-adjacent neighbors,
#          replacing the O(N^2) all-pairs scan.
#       4. A 36-slot character-histogram lower bound (L1/2 <= edit distance)
#          eliminates most surviving candidates in constant time.
#       5. Remaining candidates use a banded O(cutoff * length) Levenshtein
#          (or rapidfuzz's C++ implementation when installed) instead of the
#          full O(len_a * len_b) matrix.

#     Parameters:
#         source_dataframe (pd.DataFrame): The DataFrame to audit.
#         target_columns_subset (list[str] | None): Specific text columns to evaluate.
#             If None, candidate text columns are automatically detected.
#         similarity_threshold (float): Minimum normalized similarity score [0.0 - 1.0].
#         maximum_allowable_edit_distance (int): Maximum absolute character edits allowed.
#         minimum_character_length (int): Minimum normalized character length required
#             to be evaluated.
#         maximum_candidate_comparisons (int | None): Safety ceiling on pairwise
#             distance computations (rarely needed now; retained for compatibility).

#     Returns:
#         list[dict[str, Any]]: Detailed records of near-duplicate row pairs with the
#             same schema as the previous implementation:
#             {
#                 'row_index_first', 'row_index_second', 'evaluated_columns',
#                 'levenshtein_distance', 'similarity_score',
#                 'raw_text_first', 'raw_text_second',
#                 'normalized_string_first', 'normalized_string_second',
#                 'differing_fields_breakdown', 'matching_fields_list'
#             }
#     """
#     near_duplicate_records: list[dict[str, Any]] = []

#     if source_dataframe.empty or len(source_dataframe) < 2:
#         return near_duplicate_records

#     try:
#         # ------------------------------------------------------------------
#         # STEP 0: Resolve which text columns to evaluate.
#         # ------------------------------------------------------------------
#         evaluated_text_columns: list[str] = (
#             target_columns_subset
#             if target_columns_subset is not None and len(target_columns_subset) > 0
#             else detect_candidate_text_columns(source_dataframe)
#         )
#         if not evaluated_text_columns:
#             sys.stderr.write("[WARNING] No text columns identified for near-duplicate evaluation.\n")
#             return near_duplicate_records

#         if not RAPIDFUZZ_ACCELERATION_AVAILABLE:
#             print(
#                 "  [INFO] Optional 'rapidfuzz' package not installed. Using pure-Python "
#                 "banded Levenshtein. Install rapidfuzz for a further ~50-100x speedup: "
#                 "pip install rapidfuzz\n",
#                 flush=True,
#             )

#         # ------------------------------------------------------------------
#         # STEP 1: Vectorized normalization (single pass, no per-row iterrows).
#         # ------------------------------------------------------------------
#         raw_text_series: pd.Series = (
#             source_dataframe[evaluated_text_columns]
#             .fillna("")
#             .astype(str)
#             .agg(" ".join, axis=1)
#         )
#         normalized_text_series: pd.Series = (
#             raw_text_series.str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
#         )

#         # ------------------------------------------------------------------
#         # STEP 2: Collapse byte-identical normalized strings to one
#         # representative each (identical strings are the exact-duplicate
#         # stage's job, and comparing them here is wasted work).
#         # ------------------------------------------------------------------
#         representative_position_by_normalized_text: dict[str, int] = {}
#         for positional_index, normalized_text in enumerate(normalized_text_series.to_numpy()):
#             if len(normalized_text) < minimum_character_length:
#                 continue
#             if normalized_text not in representative_position_by_normalized_text:
#                 representative_position_by_normalized_text[normalized_text] = positional_index

#         # ------------------------------------------------------------------
#         # STEP 3: Build sorted metadata table:
#         # (length, normalized_text, positional_index, char_histogram),
#         # sorted ascending by length so the neighbor window applies.
#         # ------------------------------------------------------------------
#         sorted_candidate_metadata: list[tuple[int, str, int, tuple[int, ...]]] = sorted(
#             (
#                 (
#                     len(normalized_text),
#                     normalized_text,
#                     positional_index,
#                     build_character_frequency_histogram(normalized_text),
#                 )
#                 for normalized_text, positional_index in representative_position_by_normalized_text.items()
#             ),
#             key=lambda metadata_entry: metadata_entry[0],
#         )

#         unique_candidate_count: int = len(sorted_candidate_metadata)
#         print(
#             f"  [STATUS] Near-duplicate scan: {len(source_dataframe):,} rows -> "
#             f"{unique_candidate_count:,} unique normalized strings above length "
#             f"{minimum_character_length}. Using length-sorted neighbor window "
#             f"(max window span: {maximum_allowable_edit_distance} chars).\n",
#             flush=True,
#         )

#         progress_reporting_chunk_size: int = max(1, unique_candidate_count // 10)
#         total_distance_computations_performed: int = 0
#         comparison_budget_exhausted: bool = False

#         # ------------------------------------------------------------------
#         # STEP 4: Sorted-neighbor window scan with layered pre-filters.
#         # ------------------------------------------------------------------
#         for outer_position in range(unique_candidate_count):
#             length_a, string_a, dataframe_position_a, histogram_a = sorted_candidate_metadata[outer_position]

#             # 10% progress reporting.
#             candidates_scanned_count: int = outer_position + 1
#             if (
#                 candidates_scanned_count % progress_reporting_chunk_size == 0
#                 or candidates_scanned_count == unique_candidate_count
#             ):
#                 progress_completion_percentage: float = round(
#                     (candidates_scanned_count / unique_candidate_count) * 100.0, 1
#                 )
#                 print(
#                     f"  [STATUS] Scanned {candidates_scanned_count:,} / {unique_candidate_count:,} "
#                     f"unique strings ({progress_completion_percentage}%) | "
#                     f"{total_distance_computations_performed:,} distance computations | "
#                     f"{len(near_duplicate_records):,} pair(s) flagged...",
#                     flush=True,
#                 )

#             if comparison_budget_exhausted:
#                 break

#             for inner_position in range(outer_position + 1, unique_candidate_count):
#                 length_b, string_b, dataframe_position_b, histogram_b = sorted_candidate_metadata[inner_position]

#                 # PRE-FILTER 1 (window bound): list is length-sorted, so once the
#                 # length gap exceeds the absolute edit ceiling, no later entry
#                 # can match either. This break is what removes the O(N^2) term.
#                 if (length_b - length_a) > maximum_allowable_edit_distance:
#                     break

#                 # Per-pair effective ceiling: both the proportional similarity
#                 # threshold and the absolute edit cap must be satisfied.
#                 maximum_length: int = length_b  # length_b >= length_a by sort order
#                 ratio_based_edit_allowance: int = int(maximum_length * (1.0 - similarity_threshold))
#                 effective_maximum_edits: int = min(
#                     ratio_based_edit_allowance, maximum_allowable_edit_distance
#                 )
#                 if effective_maximum_edits == 0:
#                     continue
#                 if (length_b - length_a) > effective_maximum_edits:
#                     continue

#                 # PRE-FILTER 2 (histogram lower bound): 36 integer subtractions.
#                 # levenshtein >= L1(hist_a, hist_b) / 2, so if the L1 distance
#                 # exceeds 2 * ceiling the pair cannot match — skip the DP.
#                 histogram_l1_distance: int = 0
#                 histogram_bound_exceeded: bool = False
#                 l1_rejection_threshold: int = 2 * effective_maximum_edits
#                 for slot_index in range(36):
#                     histogram_l1_distance += abs(
#                         histogram_a[slot_index] - histogram_b[slot_index]
#                     )
#                     if histogram_l1_distance > l1_rejection_threshold:
#                         histogram_bound_exceeded = True
#                         break
#                 if histogram_bound_exceeded:
#                     continue

#                 # FULL CHECK: banded/cutoff Levenshtein.
#                 total_distance_computations_performed += 1
#                 if (
#                     maximum_candidate_comparisons is not None
#                     and total_distance_computations_performed > maximum_candidate_comparisons
#                 ):
#                     comparison_budget_exhausted = True
#                     break

#                 edit_distance: int = compute_edit_distance_with_cutoff(
#                     string_a, string_b, effective_maximum_edits
#                 )
#                 if edit_distance > effective_maximum_edits:
#                     continue

#                 # --------------------------------------------------------
#                 # MATCH FOUND: build the full report record (rare path, so
#                 # per-column .loc access cost here is negligible).
#                 # --------------------------------------------------------
#                 similarity_ratio: float = 1.0 - (edit_distance / maximum_length)
#                 actual_row_label_a: Any = source_dataframe.index[dataframe_position_a]
#                 actual_row_label_b: Any = source_dataframe.index[dataframe_position_b]
#                 row_series_a: pd.Series = source_dataframe.iloc[dataframe_position_a]
#                 row_series_b: pd.Series = source_dataframe.iloc[dataframe_position_b]

#                 differing_fields: dict[str, tuple[str, str]] = {}
#                 matching_fields: list[str] = []
#                 for column_name in source_dataframe.columns:
#                     value_a: str = str(row_series_a[column_name])
#                     value_b: str = str(row_series_b[column_name])
#                     if value_a == value_b:
#                         matching_fields.append(str(column_name))
#                     else:
#                         differing_fields[str(column_name)] = (value_a, value_b)

#                 near_duplicate_records.append(
#                     {
#                         "row_index_first": actual_row_label_a,
#                         "row_index_second": actual_row_label_b,
#                         "evaluated_columns": evaluated_text_columns,
#                         "levenshtein_distance": edit_distance,
#                         "similarity_score": round(similarity_ratio, 4),
#                         "raw_text_first": raw_text_series.iloc[dataframe_position_a],
#                         "raw_text_second": raw_text_series.iloc[dataframe_position_b],
#                         "normalized_string_first": string_a,
#                         "normalized_string_second": string_b,
#                         "differing_fields_breakdown": differing_fields,
#                         "matching_fields_list": matching_fields,
#                     }
#                 )

#         print(
#             f"\n  [COMPLETED] Near-duplicate scan finished. "
#             f"Distance computations performed: {total_distance_computations_performed:,} "
#             f"(vs. ~{(len(source_dataframe) * (len(source_dataframe) - 1)) // 2:,} brute-force pairs). "
#             f"Total pairs flagged: {len(near_duplicate_records):,}\n",
#             flush=True,
#         )
#         near_duplicate_records.sort(key=lambda record: record["similarity_score"], reverse=True)
#         return near_duplicate_records

#     except Exception:
#         sys.stderr.write(
#             f"[ERROR] An unexpected failure occurred during near-duplicate audit.\n"
#             f"Traceback:\n{traceback.format_exc()}\n"
#         )
#         return near_duplicate_records


def identify_near_duplicate_rows(
    source_dataframe: pd.DataFrame,
    target_columns_subset: list[str] | None = None,
    similarity_threshold: float = 0.98,
    maximum_allowable_edit_distance: int = 2,
    minimum_character_length: int = 15,
    maximum_candidate_comparisons: int | None = None,
    worker_process_count: int | None = None,
) -> list[dict[str, Any]]:
    """
    Identifies near-duplicate text records by evaluating exact Levenshtein edit
    distance on designated free-form text column(s). Applies both a proportional
    similarity threshold and an absolute edit distance ceiling.

    OPTIMIZED IMPLEMENTATION (sorted-neighbor window strategy):
      1. Text normalization is vectorized (single pandas pass, no iterrows).
      2. Rows with byte-identical normalized text are collapsed to a single
         representative (identical strings were already skipped by design —
         they are the exact-duplicate stage's responsibility). NOTE: this means
         if rows A and B normalize identically and row C is within threshold
         of both, one pair (representative, C) is reported rather than two
         redundant pairs — same information, fewer duplicate reports.
      3. Unique strings are sorted by length. Because an edit distance of K
         implies a length difference of at most K, each string is compared
         only against a small sliding window of length-adjacent neighbors,
         replacing the O(N^2) all-pairs scan.
      4. A 36-slot character-histogram lower bound (L1/2 <= edit distance)
         eliminates most surviving candidates in constant time.
      5. Remaining candidates use a banded O(cutoff * length) Levenshtein
         (or rapidfuzz's C++ implementation when installed) instead of the
         full O(len_a * len_b) matrix.

    PARALLEL EXECUTION (multi-process scan):
      When the unique candidate count reaches
      PARALLEL_NEAR_DUPLICATE_MINIMUM_CANDIDATE_COUNT and more than one worker
      is available, the outer-loop position range is partitioned into chunks
      and dispatched to a ProcessPoolExecutor. Each worker receives the full
      length-sorted metadata table once (via the pool initializer) and scans
      only its assigned outer range; because every unordered pair is owned by
      exactly one outer position, results are exact, complete, and free of
      duplicates regardless of chunking. If maximum_candidate_comparisons is
      set, execution deliberately stays sequential so the global comparison
      budget semantics remain exact. Any pool failure falls back to the
      sequential scan with a warning — results are never silently lost.

    Parameters:
        source_dataframe (pd.DataFrame): The DataFrame to audit.
        target_columns_subset (list[str] | None): Specific text columns to evaluate.
            If None, candidate text columns are automatically detected.
        similarity_threshold (float): Minimum normalized similarity score [0.0 - 1.0].
        maximum_allowable_edit_distance (int): Maximum absolute character edits allowed.
        minimum_character_length (int): Minimum normalized character length required
            to be evaluated.
        maximum_candidate_comparisons (int | None): Safety ceiling on pairwise
            distance computations (rarely needed now; retained for compatibility).
            Setting this forces sequential execution to keep the budget exact.
        worker_process_count (int | None): Number of parallel worker processes.
            None auto-detects (CPU cores minus one, minimum 1). A value of 1
            forces sequential execution.

    Returns:
        list[dict[str, Any]]: Detailed records of near-duplicate row pairs with the
            same schema as the previous implementation:
            {
                'row_index_first', 'row_index_second', 'evaluated_columns',
                'levenshtein_distance', 'similarity_score',
                'raw_text_first', 'raw_text_second',
                'normalized_string_first', 'normalized_string_second',
                'differing_fields_breakdown', 'matching_fields_list'
            }
    """
    near_duplicate_records: list[dict[str, Any]] = []

    if source_dataframe.empty or len(source_dataframe) < 2:
        return near_duplicate_records

    try:
        # ------------------------------------------------------------------
        # STEP 0: Resolve which text columns to evaluate.
        # ------------------------------------------------------------------
        evaluated_text_columns: list[str] = (
            target_columns_subset
            if target_columns_subset is not None and len(target_columns_subset) > 0
            else detect_candidate_text_columns(source_dataframe)
        )
        if not evaluated_text_columns:
            sys.stderr.write("[WARNING] No text columns identified for near-duplicate evaluation.\n")
            return near_duplicate_records

        if not RAPIDFUZZ_ACCELERATION_AVAILABLE:
            print(
                "  [INFO] Optional 'rapidfuzz' package not installed. Using pure-Python "
                "banded Levenshtein. Install rapidfuzz for a further ~50-100x speedup: "
                "pip install rapidfuzz\n",
                flush=True,
            )

        # ------------------------------------------------------------------
        # STEP 1: Vectorized normalization (single pass, no per-row iterrows).
        # ------------------------------------------------------------------
        raw_text_series: pd.Series[str] = (
            source_dataframe[evaluated_text_columns]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
        )
        normalized_text_series: pd.Series[str] = (
            raw_text_series.str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
        )

        # ------------------------------------------------------------------
        # STEP 2: Collapse byte-identical normalized strings to one
        # representative each (identical strings are the exact-duplicate
        # stage's job, and comparing them here is wasted work).
        # ------------------------------------------------------------------
        representative_position_by_normalized_text: dict[str, int] = {}
        for positional_index, normalized_text in enumerate(normalized_text_series.to_numpy()):
            if len(normalized_text) < minimum_character_length:
                continue
            if normalized_text not in representative_position_by_normalized_text:
                representative_position_by_normalized_text[normalized_text] = positional_index

        # ------------------------------------------------------------------
        # STEP 3: Build sorted metadata table:
        # (length, normalized_text, positional_index, char_histogram),
        # sorted ascending by length so the neighbor window applies.
        # ------------------------------------------------------------------
        sorted_candidate_metadata: list[tuple[int, str, int, tuple[int, ...]]] = sorted(
            (
                (
                    len(normalized_text),
                    normalized_text,
                    positional_index,
                    build_character_frequency_histogram(normalized_text),
                )
                for normalized_text, positional_index in representative_position_by_normalized_text.items()
            ),
            key=lambda metadata_entry: metadata_entry[0],
        )

        unique_candidate_count: int = len(sorted_candidate_metadata)
        resolved_worker_process_count: int = resolve_worker_process_count(worker_process_count)

        parallel_execution_enabled: bool = (
            maximum_candidate_comparisons is None
            and unique_candidate_count >= PARALLEL_NEAR_DUPLICATE_MINIMUM_CANDIDATE_COUNT
            and resolved_worker_process_count > 1
        )

        print(
            f"  [STATUS] Near-duplicate scan: {len(source_dataframe):,} rows -> "
            f"{unique_candidate_count:,} unique normalized strings above length "
            f"{minimum_character_length}. Using length-sorted neighbor window "
            f"(max window span: {maximum_allowable_edit_distance} chars). "
            f"Execution mode: "
            f"{f'PARALLEL ({resolved_worker_process_count} worker processes)' if parallel_execution_enabled else 'SEQUENTIAL (single process)'}.\n",
            flush=True,
        )

        matched_pair_tuples: list[tuple[int, int, int, int]] = []
        total_distance_computations_performed: int = 0

        # ------------------------------------------------------------------
        # STEP 4-P: PARALLEL sorted-neighbor window scan (process pool).
        # ------------------------------------------------------------------
        if parallel_execution_enabled:
            try:
                # Partition the outer position range into more chunks than
                # workers so faster workers pick up remaining chunks (basic
                # dynamic load balancing without shared state).
                chunk_count: int = resolved_worker_process_count * 4
                base_chunk_size: int = max(1, unique_candidate_count // chunk_count)
                outer_position_chunk_ranges: list[tuple[int, int]] = [
                    (chunk_start, min(chunk_start + base_chunk_size, unique_candidate_count))
                    for chunk_start in range(0, unique_candidate_count, base_chunk_size)
                ]
                total_chunk_count: int = len(outer_position_chunk_ranges)
                completed_chunk_count: int = 0

                with concurrent.futures.ProcessPoolExecutor(
                    max_workers=resolved_worker_process_count,
                    initializer=_initialize_near_duplicate_worker_process,
                    initargs=(
                        sorted_candidate_metadata,
                        similarity_threshold,
                        maximum_allowable_edit_distance,
                    ),
                ) as process_pool_executor:
                    pending_chunk_futures = [
                        process_pool_executor.submit(_scan_near_duplicate_chunk_in_worker, chunk_range)
                        for chunk_range in outer_position_chunk_ranges
                    ]
                    for completed_future in concurrent.futures.as_completed(pending_chunk_futures):
                        chunk_pair_tuples, chunk_computation_count = completed_future.result()
                        matched_pair_tuples.extend(chunk_pair_tuples)
                        total_distance_computations_performed += chunk_computation_count
                        completed_chunk_count += 1
                        print(
                            f"  [STATUS] Parallel chunk {completed_chunk_count:,} / {total_chunk_count:,} "
                            f"complete | {total_distance_computations_performed:,} distance computations | "
                            f"{len(matched_pair_tuples):,} pair(s) flagged...",
                            flush=True,
                        )
            except Exception:
                # A pool failure (e.g., pickling error, worker crash, restricted
                # environment without fork/spawn) must never lose results:
                # report loudly and rerun the entire scan sequentially.
                sys.stderr.write(
                    f"[WARNING] Parallel near-duplicate scan failed; falling back to "
                    f"sequential single-process scan. Root cause:\n{traceback.format_exc()}\n"
                )
                matched_pair_tuples = []
                total_distance_computations_performed = 0
                parallel_execution_enabled = False

        # ------------------------------------------------------------------
        # STEP 4-S: SEQUENTIAL scan (small inputs, budget mode, or fallback).
        # ------------------------------------------------------------------
        if not parallel_execution_enabled:

            def sequential_progress_report_callback(
                outer_positions_scanned: int,
                distance_computations: int,
                pairs_found: int,
            ) -> None:
                """Prints 10%-interval progress lines for the sequential scan."""
                progress_completion_percentage: float = round(
                    (outer_positions_scanned / unique_candidate_count) * 100.0, 1
                ) if unique_candidate_count > 0 else 100.0
                print(
                    f"  [STATUS] Scanned {outer_positions_scanned:,} / {unique_candidate_count:,} "
                    f"unique strings ({progress_completion_percentage}%) | "
                    f"{distance_computations:,} distance computations | "
                    f"{pairs_found:,} pair(s) flagged...",
                    flush=True,
                )

            matched_pair_tuples, total_distance_computations_performed = (
                scan_candidate_position_range_for_near_duplicate_pairs(
                    sorted_candidate_metadata=sorted_candidate_metadata,
                    outer_position_range_start=0,
                    outer_position_range_end=unique_candidate_count,
                    similarity_threshold=similarity_threshold,
                    maximum_allowable_edit_distance=maximum_allowable_edit_distance,
                    maximum_candidate_comparisons=maximum_candidate_comparisons,
                    progress_report_callback=sequential_progress_report_callback,
                )
            )

        # ------------------------------------------------------------------
        # STEP 5: Build the full report records from matched position tuples.
        # This is a rare path (matches only), so per-row DataFrame access
        # cost here is negligible, and it runs once regardless of scan mode.
        # ------------------------------------------------------------------
        for outer_metadata_position, inner_metadata_position, edit_distance, maximum_length in matched_pair_tuples:
            _, string_a, dataframe_position_a, _ = sorted_candidate_metadata[outer_metadata_position]
            _, string_b, dataframe_position_b, _ = sorted_candidate_metadata[inner_metadata_position]

            similarity_ratio: float = 1.0 - (edit_distance / maximum_length)
            actual_row_label_a: Any = source_dataframe.index[dataframe_position_a]
            actual_row_label_b: Any = source_dataframe.index[dataframe_position_b]
            row_series_a: pd.Series[Any] = source_dataframe.iloc[dataframe_position_a]
            row_series_b: pd.Series[Any] = source_dataframe.iloc[dataframe_position_b]

            differing_fields: dict[str, tuple[str, str]] = {}
            matching_fields: list[str] = []
            for column_name in source_dataframe.columns:
                value_a: str = str(row_series_a[column_name])
                value_b: str = str(row_series_b[column_name])
                if value_a == value_b:
                    matching_fields.append(str(column_name))
                else:
                    differing_fields[str(column_name)] = (value_a, value_b)

            near_duplicate_records.append(
                {
                    "row_index_first": actual_row_label_a,
                    "row_index_second": actual_row_label_b,
                    "evaluated_columns": evaluated_text_columns,
                    "levenshtein_distance": edit_distance,
                    "similarity_score": round(similarity_ratio, 4),
                    "raw_text_first": raw_text_series.iloc[dataframe_position_a],
                    "raw_text_second": raw_text_series.iloc[dataframe_position_b],
                    "normalized_string_first": string_a,
                    "normalized_string_second": string_b,
                    "differing_fields_breakdown": differing_fields,
                    "matching_fields_list": matching_fields,
                }
            )

        print(
            f"\n  [COMPLETED] Near-duplicate scan finished. "
            f"Distance computations performed: {total_distance_computations_performed:,} "
            f"(vs. ~{(len(source_dataframe) * (len(source_dataframe) - 1)) // 2:,} brute-force pairs). "
            f"Total pairs flagged: {len(near_duplicate_records):,}\n",
            flush=True,
        )
        near_duplicate_records.sort(key=lambda record: record["similarity_score"], reverse=True)
        return near_duplicate_records

    except Exception:
        sys.stderr.write(
            f"[ERROR] An unexpected failure occurred during near-duplicate audit.\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        return near_duplicate_records


def cluster_near_duplicate_records_into_connected_groups(
    near_duplicate_records: list[dict[str, Any]],
    source_dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Aggregates pairwise near-duplicate records into transitively connected
    groups using breadth-first graph traversal.

    For example, if Row 14 matches Row 82, and Row 82 matches Row 305, this function
    unifies {Row 14, Row 82, Row 305} into a single connected group. All member
    rows within each group are ordered strictly by their appearance in the dataset
    (top-to-bottom index order), ensuring that the first element is the earliest row
    in the file and the last element is the latest row in the file.

    Parameters:
        near_duplicate_records (list[dict[str, Any]]): List of pairwise near-duplicate
            records emitted by the distance detection stage.
        source_dataframe (pd.DataFrame): The source DataFrame being audited, used
            to establish the original top-to-bottom row index order.

    Returns:
        list[dict[str, Any]]: A list of cluster dictionaries, each containing:
            - 'group_identifier' (int): 1-based unique identifier for the group.
            - 'member_row_indices_in_dataset_order' (list[Any]): List of DataFrame
              index labels in this group, ordered from earliest to latest row in the file.
            - 'member_row_count' (int): Total number of rows belonging to this group.
            - 'associated_pairwise_record_count' (int): Number of pairwise matches within this group.
    """
    if not near_duplicate_records:
        return []

    try:
        # Build adjacency graph representing all pairwise near-duplicate links
        adjacency_graph_by_row_index: dict[Any, set[Any]] = defaultdict(set)
        for pairwise_record in near_duplicate_records:
            first_row_label: Any = pairwise_record["row_index_first"]
            second_row_label: Any = pairwise_record["row_index_second"]
            adjacency_graph_by_row_index[first_row_label].add(second_row_label)
            adjacency_graph_by_row_index[second_row_label].add(first_row_label)

        visited_row_indices_set: set[Any] = set()
        connected_groups_summary_list: list[dict[str, Any]] = []

        # Iterate through the DataFrame's original index order to discover components
        for candidate_start_row_index in source_dataframe.index:
            if (
                candidate_start_row_index in adjacency_graph_by_row_index
                and candidate_start_row_index not in visited_row_indices_set
            ):
                current_component_indices_list: list[Any] = []
                traversal_queue: list[Any] = [candidate_start_row_index]
                visited_row_indices_set.add(candidate_start_row_index)

                while traversal_queue:
                    current_node_index: Any = traversal_queue.pop(0)
                    current_component_indices_list.append(current_node_index)

                    for neighbor_node_index in adjacency_graph_by_row_index[current_node_index]:
                        if neighbor_node_index not in visited_row_indices_set:
                            visited_row_indices_set.add(neighbor_node_index)
                            traversal_queue.append(neighbor_node_index)

                # Order member indices strictly by their position in the source DataFrame
                component_indices_set: set[Any] = set(current_component_indices_list)
                ordered_member_row_indices: list[Any] = [
                    row_index
                    for row_index in source_dataframe.index
                    if row_index in component_indices_set
                ]

                # Count the internal pairwise links within this connected component
                internal_pairwise_links_count: int = sum(
                    1
                    for pairwise_record in near_duplicate_records
                    if pairwise_record["row_index_first"] in component_indices_set
                    and pairwise_record["row_index_second"] in component_indices_set
                )

                group_record_dictionary: dict[str, Any] = {
                    "group_identifier": len(connected_groups_summary_list) + 1,
                    "member_row_indices_in_dataset_order": ordered_member_row_indices,
                    "member_row_count": len(ordered_member_row_indices),
                    "associated_pairwise_record_count": internal_pairwise_links_count,
                }
                connected_groups_summary_list.append(group_record_dictionary)

        return connected_groups_summary_list

    except Exception:
        sys.stderr.write(
            f"[ERROR] An unexpected error occurred while clustering near-duplicates into groups.\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        return []

# =====================================================================
# SECTION 5: TRAIN / TEST SPLIT INTEGRITY & LEAKAGE AUDIT (PART B)
# =====================================================================


def audit_train_test_split_integrity(
    training_dataframe: pd.DataFrame,
    testing_dataframe: pd.DataFrame,
    target_column_identifier: str | None = None,
) -> dict[str, Any]:
    """
    Executes a comprehensive, non-destructive audit between a training dataset
    and a testing dataset to detect schema divergence, train-test data leakage,
    and novel categorical values in test data.

    Parameters:
        training_dataframe (pd.DataFrame): The reference training partition.
        testing_dataframe (pd.DataFrame): The evaluation testing partition.
        target_column_identifier (str | None): Target label column name to exclude if necessary.

    Returns:
        dict[str, Any]: Detailed dictionary containing verification findings.
    """
    audit_findings_report: dict[str, Any] = {}

    try:
        train_column_names_set: set[str] = set(str(col) for col in training_dataframe.columns)
        test_column_names_set: set[str] = set(str(col) for col in testing_dataframe.columns)

        # 1. Schema Alignment Verification
        columns_exclusive_to_train: set[str] = train_column_names_set - test_column_names_set
        columns_exclusive_to_test: set[str] = test_column_names_set - train_column_names_set
        mutually_shared_columns: list[str] = sorted(list(train_column_names_set & test_column_names_set))

        audit_findings_report["schema_alignment"] = {
            "training_column_count": len(train_column_names_set),
            "testing_column_count": len(test_column_names_set),
            "columns_exclusive_to_train": sorted(list(columns_exclusive_to_train)),
            "columns_exclusive_to_test": sorted(list(columns_exclusive_to_test)),
            "mutually_shared_columns_count": len(mutually_shared_columns),
        }

        # 2. Data Contamination / Leakage Detection (Shared Row Hashes)
        train_features_dataframe: pd.DataFrame = training_dataframe[mutually_shared_columns]
        test_features_dataframe: pd.DataFrame = testing_dataframe[mutually_shared_columns]

        train_row_hashes_series: pd.Series = pd.util.hash_pandas_object(train_features_dataframe, index=False)
        test_row_hashes_series: pd.Series = pd.util.hash_pandas_object(test_features_dataframe, index=False)

        train_hash_set: set[int] = set(train_row_hashes_series)
        test_hash_set: set[int] = set(test_row_hashes_series)

        leaked_row_hashes: set[int] = train_hash_set.intersection(test_hash_set)
        test_rows_leaked_count: int = int(test_row_hashes_series.isin(leaked_row_hashes).sum())
        leakage_percentage: float = (
            (test_rows_leaked_count / len(testing_dataframe) * 100.0) if len(testing_dataframe) > 0 else 0.0
        )

        audit_findings_report["data_leakage_contamination"] = {
            "leaked_unique_row_signatures_count": len(leaked_row_hashes),
            "contaminated_test_sample_count": test_rows_leaked_count,
            "contaminated_test_percentage": round(leakage_percentage, 2),
        }

        # 3. Novel Categorical Values Verification
        unseen_categorical_levels_report: dict[str, list[Any]] = {}

        for column_name in mutually_shared_columns:
            if column_name == target_column_identifier:
                continue

            train_series_dtype = training_dataframe[column_name].dtype
            test_series_dtype = testing_dataframe[column_name].dtype

            if train_series_dtype == "object" or test_series_dtype == "object":
                train_unique_values: set[Any] = set(training_dataframe[column_name].dropna().unique())
                test_unique_values: set[Any] = set(testing_dataframe[column_name].dropna().unique())

                unseen_test_values: set[Any] = test_unique_values - train_unique_values

                if len(unseen_test_values) > 0:
                    unseen_categorical_levels_report[column_name] = sorted(list(unseen_test_values))[:20]

        audit_findings_report["unseen_categorical_values_in_test"] = unseen_categorical_levels_report

        return audit_findings_report

    except Exception:
        sys.stderr.write(
            f"[ERROR] An unexpected error occurred during train/test split audit.\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        return audit_findings_report


# =====================================================================
# SECTION 6: REPORTING AND FORMATTED VISUALIZATION
# =====================================================================


def print_section_divider(header_title: str) -> None:
    """Prints a formatted terminal section header banner."""
    print("\n" + "=" * 80)
    print(f"  {header_title.upper()}")
    print("=" * 80)


def display_single_dataset_audit_report(
    source_file_path: str,
    source_dataframe: pd.DataFrame,
    malformed_rows_list: list[dict[str, int]],
    mixed_types_report: dict[str, dict[str, int]],
    standard_describe_dataframe: pd.DataFrame,
    extended_metrics_report: dict[str, dict[str, Any]],
    exact_duplicates_report: dict[str, Any],
    near_duplicates_report: list[dict[str, Any]],
) -> None:
    """
    Renders a comprehensive, structured text report of all diagnostics
    to standard console output.
    """
    print_section_divider(f"AUDIT SUMMARY FOR: {os.path.basename(source_file_path)}")
    print(f"File Path: {source_file_path}")
    print(f"Total Rows: {len(source_dataframe):,} | Total Columns: {len(source_dataframe.columns):,}")

    # 1. Malformed Rows Output
    print_section_divider("1. Malformed Rows Diagnostic")
    if len(malformed_rows_list) == 0:
        print("Status: Clean. No line-level field count discrepancies detected.")
    else:
        print(f"Status: ANOMALIES FOUND! Detected {len(malformed_rows_list):,} malformed row(s).")
        for record in malformed_rows_list[:10]:
            print(
                f"  - Line {record['line_number']}: Expected {record['expected_field_count']} fields, "
                f"Observed {record['observed_field_count']} fields."
            )
        if len(malformed_rows_list) > 10:
            print(f"  ... [and {len(malformed_rows_list) - 10} additional malformed lines]")

    # 2. Mixed Data Types Output
    print_section_divider("2. Column Data Types & Mixed-Type Diagnostic")
    if len(mixed_types_report) == 0:
        print("Status: Clean. No mixed-type object columns detected.")
    else:
        print(f"Status: MIXED TYPES DETECTED in {len(mixed_types_report)} column(s):")
        for column_name, type_breakdown in mixed_types_report.items():
            breakdown_string: str = ", ".join([f"{type_name}: {count}" for type_name, count in type_breakdown.items()])
            print(f"  - Column '{column_name}': [{breakdown_string}]")

    # 3. Descriptive Statistics & Extended Column Health
    print_section_divider("3. Column Health & Extended Descriptive Metrics")
    print(f"{'Column Name':<25} {'Dtype':<10} {'Nulls':<10} {'Null %':<10} {'Whitespace':<12} {'Distinct':<10}")
    print("-" * 80)
    for column_name, metrics in extended_metrics_report.items():
        print(
            f"{column_name[:24]:<25} "
            f"{metrics['pandas_dtype'][:9]:<10} "
            f"{metrics['missing_value_count']:<10} "
            f"{metrics['missing_value_percentage']:<10} "
            f"{metrics['whitespace_only_cell_count']:<12} "
            f"{metrics['unique_value_count']:<10}"
        )

    if not standard_describe_dataframe.empty:
        print("\nStandard Statistical Description (.describe()):")
        print(standard_describe_dataframe.to_string())

    # 4. Exact Duplicates Output
    print_section_divider("4. Exact Duplicate Rows Diagnostic (Hash-Based)")
    exact_count: int = exact_duplicates_report["total_duplicate_rows_count"]
    cluster_count: int = exact_duplicates_report["duplicate_cluster_count"]
    if exact_count == 0:
        print("Status: Clean. No exact duplicate rows identified.")
    else:
        print(f"Status: IDENTIFIED {exact_count:,} duplicate rows across {cluster_count:,} unique cluster(s).")
        for cluster_index, indices in enumerate(exact_duplicates_report["duplicate_index_clusters"][:5], start=1):
            print(f"  - Duplicate Cluster #{cluster_index}: Row Indices {indices[:8]}{'...' if len(indices)>8 else ''}")
        if cluster_count > 5:
            print(f"  ... [and {cluster_count - 5} additional duplicate clusters]")

    # 5. Near-Duplicate Rows Output (Exact Levenshtein Distance Breakdown)
    print_section_divider("5. Near-Duplicate Diagnostic (Alphanumeric Normalized Levenshtein)")
    if len(near_duplicates_report) == 0:
        print("Status: Clean. No near-duplicate rows found within similarity threshold.")
    else:
        print(f"Status: FLAGGED {len(near_duplicates_report):,} near-duplicate pair(s):\n")

        display_limit: int = 10
        for pair_index, record in enumerate(near_duplicates_report[:display_limit], start=1):
            similarity_pct: float = round(record["similarity_score"] * 100.0, 2)
            distance: int = record["levenshtein_distance"]
            row_a: Any = record["row_index_first"]
            row_b: Any = record["row_index_second"]
            differing: dict[str, tuple[str, str]] = record["differing_fields_breakdown"]
            matching: list[str] = record["matching_fields_list"]

            print(f"  ┌─ Match Pair #{pair_index}")
            print(f"  │  Row Indices:               [{row_a}] <---> [{row_b}]")
            print(f"  │  Similarity Score:          {similarity_pct}%")
            print(f"  │  Exact Levenshtein Edits:   {distance} character edit(s)")
            print(f"  │  Normalized String A:       \"{record['normalized_string_first']}\"")
            print(f"  │  Normalized String B:       \"{record['normalized_string_second']}\"")
            print(f"  │  Identical Fields ({len(matching)}):     {', '.join(matching) if matching else '[None]'}")
            print(f"  │  Diverging Fields ({len(differing)}):")
            for col, (val_a, val_b) in differing.items():
                print(f"  │    • Column '{col}':")
                print(f"  │        Row [{row_a}]: \"{val_a}\"")
                print(f"  │        Row [{row_b}]: \"{val_b}\"")
            print("  └" + "─" * 70)

        if len(near_duplicates_report) > display_limit:
            print(f"\n  ... [and {len(near_duplicates_report) - display_limit:,} additional near-duplicate pairs not shown]")


def display_train_test_audit_report(
    training_file_path: str,
    testing_file_path: str,
    audit_findings_report: dict[str, Any],
) -> None:
    """Renders the train/test comparative audit report."""
    print_section_divider("TRAIN / TEST SPLIT INTEGRITY VERIFICATION REPORT")
    print(f"Training Partition Path: {training_file_path}")
    print(f"Testing Partition Path:  {testing_file_path}")

    # Schema Alignment
    schema_info: dict[str, Any] = audit_findings_report.get("schema_alignment", {})
    print_section_divider("1. Schema & Feature Alignment")
    print(f"Training Column Count: {schema_info.get('training_column_count', 0)}")
    print(f"Testing Column Count:  {schema_info.get('testing_column_count', 0)}")
    print(f"Mutually Shared Count: {schema_info.get('mutually_shared_columns_count', 0)}")

    missing_in_test: list[str] = schema_info.get("columns_exclusive_to_train", [])
    if missing_in_test:
        print(f"\n[WARNING] Columns present in TRAIN but MISSING in TEST ({len(missing_in_test)}):")
        for col in missing_in_test:
            print(f"  - {col}")

    missing_in_train: list[str] = schema_info.get("columns_exclusive_to_test", [])
    if missing_in_train:
        print(f"\n[WARNING] Columns present in TEST but MISSING in TRAIN ({len(missing_in_train)}):")
        for col in missing_in_train:
            print(f"  - {col}")

    # Data Leakage
    leakage_info: dict[str, Any] = audit_findings_report.get("data_leakage_contamination", {})
    print_section_divider("2. Data Leakage / Contamination Diagnostic")
    contaminated_count: int = leakage_info.get("contaminated_test_sample_count", 0)
    contaminated_pct: float = leakage_info.get("contaminated_test_percentage", 0.0)
    if contaminated_count == 0:
        print("Status: Clean. Zero exact row leakage detected between train and test partitions.")
    else:
        print(
            f"Status: LEAKAGE DETECTED!\n"
            f"  - {contaminated_count:,} test partition samples ({contaminated_pct}%) are completely "
            f"identical to training samples across shared features."
        )

    # Unseen Categorical Levels
    unseen_cats: dict[str, list[Any]] = audit_findings_report.get("unseen_categorical_values_in_test", {})
    print_section_divider("3. Novel Categorical Values Diagnostic (In Test But Absent in Train)")
    if len(unseen_cats) == 0:
        print("Status: Clean. No novel categorical values found in test features.")
    else:
        print(f"Status: UNSEEN CATEGORICAL VALUES DETECTED in {len(unseen_cats)} column(s):")
        for column_name, unseen_values in unseen_cats.items():
            print(f"  - Column '{column_name}': {len(unseen_values)} novel value(s) -> {unseen_values}")


# =====================================================================
# SECTION 7: INTERACTIVE Q&A CONFIGURATION & REMEDIATION (PART A.6, C)
# =====================================================================

def prompt_near_duplicate_configuration(
    source_dataframe: pd.DataFrame,
) -> tuple[bool, float, int, str | None]:
    """
    Prompts the user interactively to determine whether to execute near-duplicate
    distance matching, what strictness tier to apply, and presents a numbered catalog
    of all dataset columns with their pandas dtypes and sample values for selection.

    Parameters:
        source_dataframe (pd.DataFrame): The DataFrame being audited.

    Returns:
        tuple[bool, float, int, str | None]:
            1. execute_check (bool): Whether to run near-duplicate detection.
            2. similarity_threshold (float): Configured minimum similarity ratio (0.0 - 1.0).
            3. max_allowable_edits (int): Configured maximum absolute edit distance.
            4. target_column_name (str | None): The selected column name for distance checks.
    """
    print_section_divider("NEAR-DUPLICATE / DISTANCE MATCHING CONFIGURATION")
    run_check_selection: str = prompt_user_selection(
        "Execute near-duplicate / Levenshtein distance check?",
        ["y", "n"],
        "y",
    )

    if run_check_selection == "n":
        return False, 0.98, 2, None

    print("\nSelect Near-Duplicate Strictness Tier:")
    print("  [1] Ultra-Strict (98% similarity, max 2 character edits) [DEFAULT]")
    print("  [2] Strict       (95% similarity, max 4 character edits)")
    print("  [3] Custom       (Enter manual similarity ratio and edit ceiling)")
    print("  [4] Skip Check   (Do not run distance matching)")

    tier_choice: str = prompt_user_selection(
        "Choose strictness tier",
        ["1", "2", "3", "4"],
        "1",
    )

    if tier_choice == "4":
        return False, 0.98, 2, None

    if tier_choice == "1":
        similarity_threshold = 0.98
        max_allowable_edits = 2
    elif tier_choice == "2":
        similarity_threshold = 0.95
        max_allowable_edits = 4
    else:
        # Custom parameters input
        while True:
            ratio_input: str = input("Enter minimum similarity threshold [0.50 - 0.99] (Default: 0.98): ").strip()
            if not ratio_input:
                similarity_threshold = 0.98
                break
            try:
                ratio_val: float = float(ratio_input)
                if 0.50 <= ratio_val <= 1.0:
                    similarity_threshold = ratio_val
                    break
                print("Threshold must be between 0.50 and 1.0.")
            except ValueError:
                print("Invalid entry. Please enter a valid decimal number (e.g. 0.97).")

        while True:
            edits_input: str = input("Enter maximum allowable character edits [1 - 20] (Default: 2): ").strip()
            if not edits_input:
                max_allowable_edits = 2
                break
            try:
                edits_val: int = int(edits_input)
                if edits_val >= 1:
                    max_allowable_edits = edits_val
                    break
                print("Max edits must be a positive integer (>= 1).")
            except ValueError:
                print("Invalid entry. Please enter a valid integer.")

    # Numbered column catalog with Dtype and Sample Data
    all_column_names: list[str] = list(source_dataframe.columns)
    candidate_text_columns_set: set[str] = set(detect_candidate_text_columns(source_dataframe))

    print("\n" + "=" * 80)
    print("  AVAILABLE DATASET COLUMNS")
    print("=" * 80)
    print(f"  {'#':<4} {'Column Name':<26} {'Dtype':<12} {'Sample Data'}")
    print("  " + "-" * 76)

    default_column_index: int = 1
    for index_counter, column_name in enumerate(all_column_names, start=1):
        column_dtype_string: str = str(source_dataframe[column_name].dtype)
        non_null_samples: pd.Series = source_dataframe[column_name].dropna()

        if not non_null_samples.empty:
            sample_value_display: str = repr(str(non_null_samples.iloc[0])[:35])
        else:
            sample_value_display = "<All NaN / Empty>"

        is_suggested: bool = column_name in candidate_text_columns_set
        marker_tag: str = " [Suggested text]" if is_suggested else ""

        # Set default to the first suggested text column found
        if is_suggested and default_column_index == 1:
            default_column_index = index_counter

        print(
            f"  [{index_counter:<2}] {column_name[:25]:<26} "
            f"{column_dtype_string[:11]:<12} "
            f"{sample_value_display}{marker_tag}"
        )

    # Prompt user to choose by column number
    while True:
        column_selection_input: str = input(
            f"\nTEXT: Select text column number to evaluate (1 - {len(all_column_names)}) (Default: [{default_column_index}] {all_column_names[default_column_index - 1]}): "
        ).strip()

        if not column_selection_input:
            target_column_name: str | None = all_column_names[default_column_index - 1]
            break

        if column_selection_input.isdigit():
            selected_number: int = int(column_selection_input)
            if 1 <= selected_number <= len(all_column_names):
                target_column_name = all_column_names[selected_number - 1]
                break
            print(f"Selection out of range. Please choose a number between 1 and {len(all_column_names)}.")
        elif column_selection_input in all_column_names:
            target_column_name = column_selection_input
            break
        else:
            print(
                f"Invalid selection '{column_selection_input}'. Please enter a column number from the list above."
            )

    print(f"\n[CONFIRMED] Target Column Selected for Distance Matching: '{target_column_name}'")
    return True, similarity_threshold, max_allowable_edits, target_column_name

def prompt_user_selection(prompt_text: str, valid_choices: list[str], default_choice: str) -> str:
    """Utility to prompt for interactive terminal input with validation."""
    valid_choices_lower: list[str] = [choice.lower() for choice in valid_choices]
    while True:
        user_response: str = input(f"{prompt_text} [{'/'.join(valid_choices)}] (Default: {default_choice}): ").strip()
        if not user_response:
            return default_choice.lower()
        if user_response.lower() in valid_choices_lower:
            return user_response.lower()
        print(f"Invalid selection. Please choose one of: {valid_choices}")


def prompt_interactive_cleaning_configuration(
    source_dataframe: pd.DataFrame,
    exact_duplicates_report: dict[str, Any],
    mixed_types_report: dict[str, dict[str, int]],
    near_duplicates_report: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Presents an interactive terminal Q&A wizard guiding the user through
    cleaning transformations, multi-class label binarization, null column
    filtering thresholds, and export destination configuration.

    Parameters:
        source_dataframe (pd.DataFrame): The audited DataFrame to evaluate.
        exact_duplicates_report (dict[str, Any]): Exact duplicates report containing
            duplicate counts and index clusters.
        mixed_types_report (dict[str, dict[str, int]]): Mixed types report mapping
            column names to frequency distributions of coexisting Python types.
        near_duplicates_report (list[dict[str, Any]] | None): Detected near-duplicate
            pairs report with similarity scores and field diffs.

    Returns:
        dict[str, Any]: Structured cleaning configuration dictionary containing:
            - 'drop_exact_duplicates' (bool): Flag indicating duplicate row removal.
            - 'duplicate_retention_strategy' (str): Retention rule ('first', 'last', 'none').
            - 'near_duplicate_indices_to_drop' (set[Any]): Specific row indices to remove.
            - 'mixed_type_remediation_actions' (dict[str, str]): Per-column coercion rules.
            - 'binary_class_conversion' (dict[str, Any]): Settings for converting a multi-class
              column to binary [0, 1] integer representation.
            - 'drop_null_threshold_columns_percentage' (float): Column null drop threshold.
            - 'export_format' (str): Target export format ('csv', 'jsonl', 'json').
            - 'export_delimiter' (str): Separator character for CSV exports.
            - 'target_output_file_path' (str): Destination path for written files.
    """
    print_section_divider("DATASET REMEDIATION & EXPORT CONFIGURATION WIZARD")

    # Initialize the centralized configuration dictionary with standard default settings
    remediation_config: dict[str, Any] = {
            "drop_exact_duplicates": False,
            "duplicate_retention_strategy": "first",
            "near_duplicate_indices_to_drop": set(),
            "mixed_type_remediation_actions": {},
            "binary_class_conversion": {
                "enabled": False,
                "target_column_name": "",
                "zero_class_values_list": [],
                "one_class_values_list": [],
            },
            "designated_text_column": None,
            "designated_label_column": None,
            "displaced_column_renames": {},
            "drop_null_threshold_columns_percentage": 100.0,
            "export_format": "jsonl",
            "export_delimiter": ",",
            "target_output_file_path": "",
        }

    # =========================================================================
    # STEP 1: Exact Duplicate Row Handling
    # =========================================================================
    if exact_duplicates_report["total_duplicate_rows_count"] > 0:
        drop_duplicates_choice: str = prompt_user_selection(
            "Exact duplicates detected. Would you like to drop duplicate rows?",
            ["y", "n"],
            "y",
        )
        if drop_duplicates_choice == "y":
            remediation_config["drop_exact_duplicates"] = True
            strategy_choice: str = prompt_user_selection(
                "Which duplicate occurrence should be preserved?",
                ["first", "last", "none"],
                "first",
            )
            remediation_config["duplicate_retention_strategy"] = strategy_choice

    # # =========================================================================
    # # STEP 2: Near-Duplicate Row Resolution
    # # =========================================================================
    # if near_duplicates_report and len(near_duplicates_report) > 0:
    #     total_near_duplicate_pairs_count: int = len(near_duplicates_report)
    #     print(f"\n[NEAR-DUPLICATE REMEDIATION] Detected {total_near_duplicate_pairs_count} near-duplicate pair(s).")

    #     auto_resolve_choice: str = prompt_user_selection(
    #         "Auto resolve (keep one of each), or manual handling?",
    #         ["y", "n"],
    #         "n",
    #     )

    #     indices_to_drop_set: set[Any] = set()

    #     if auto_resolve_choice == "y":
    #         for pair_record in near_duplicates_report:
    #             secondary_row_index: Any = pair_record["row_index_second"]
    #             indices_to_drop_set.add(secondary_row_index)
    #         print(f"[AUTO RESOLVE] Marked {len(indices_to_drop_set)} secondary row(s) for removal.")
    #     else:
    #         print("\nManual Pair-by-Pair Resolution:")
    #         for pair_index, pair_record in enumerate(near_duplicates_report, start=1):
    #             row_index_first: Any = pair_record["row_index_first"]
    #             row_index_second: Any = pair_record["row_index_second"]
    #             similarity_percentage: float = round(pair_record["similarity_score"] * 100.0, 2)
    #             edit_distance_count: int = pair_record["levenshtein_distance"]

    #             print(
    #                 f"\n  Pair #{pair_index}: Row [{row_index_first}] <---> Row [{row_index_second}] "
    #                 f"(Similarity: {similarity_percentage}%, Edits: {edit_distance_count})"
    #             )
    #             print(f"    [a] Keep Row [{row_index_first}] (drop Row [{row_index_second}])")
    #             print(f"    [b] Keep Row [{row_index_second}] (drop Row [{row_index_first}])")
    #             print("    [d] Drop both rows")
    #             print("    [k] Keep both rows (skip / ignore this pair)")

    #             pair_action_choice: str = prompt_user_selection(
    #                 f"Action for Pair #{pair_index}",
    #                 ["a", "b", "d", "k"],
    #                 "k",
    #             )

    #             if pair_action_choice == "a":
    #                 indices_to_drop_set.add(row_index_second)
    #             elif pair_action_choice == "b":
    #                 indices_to_drop_set.add(row_index_first)
    #             elif pair_action_choice == "d":
    #                 indices_to_drop_set.add(row_index_first)
    #                 indices_to_drop_set.add(row_index_second)
    #             elif pair_action_choice == "k":
    #                 pass

    #     remediation_config["near_duplicate_indices_to_drop"] = indices_to_drop_set

    # =========================================================================
    # STEP 2: Near-Duplicate Group Resolution (Bulk & Individual Options)
    # =========================================================================
    if near_duplicates_report and len(near_duplicates_report) > 0:
        remediation_config["near_duplicate_indices_to_drop"] = (
            prompt_near_duplicate_group_resolution(
                source_dataframe=source_dataframe,
                near_duplicate_records=near_duplicates_report,
                evaluated_text_column_name=remediation_config.get("designated_text_column"),
            )
        )

    # =========================================================================
    # STEP 3: Mixed Data Type Remediation
    # =========================================================================
    if len(mixed_types_report) > 0:
        print("\nMixed-type columns require remediation strategy:")
        for column_name in mixed_types_report:
            print(f"\nColumn: '{column_name}' with types: {mixed_types_report[column_name]}")
            action_choice: str = prompt_user_selection(
                f"Select conversion strategy for '{column_name}'",
                ["keep", "numeric", "string"],
                "string",
            )
            remediation_config["mixed_type_remediation_actions"][column_name] = action_choice

    # =========================================================================
    # STEP 4: Select 'text' & 'label' Columns (With Conflict Check & Binarization)
    # =========================================================================
    print_section_divider("SELECT 'TEXT' AND 'LABEL' COLUMNS")
    available_cols: list[str] = list(source_dataframe.columns)
    total_columns_count: int = len(available_cols)

    print("Available dataset columns:")
    for idx, col_name in enumerate(available_cols, start=1):
        dtype_str: str = str(source_dataframe[col_name].dtype)
        distinct_count: int = int(source_dataframe[col_name].nunique(dropna=True))
        print(f"  [{idx:<2}] {col_name:<30} Dtype: {dtype_str:<10} Distinct Values: {distinct_count}")

    # 1. Ask user to pick the TEXT column
    while True:
        text_choice: str = input(f"\nTEXT: Select column number for 'text' (1 - {total_columns_count}): ").strip()
        if text_choice.isdigit() and 1 <= int(text_choice) <= total_columns_count:
            chosen_text_col: str = available_cols[int(text_choice) - 1]
            break
        print(f"Invalid input. Please enter a number between 1 and {total_columns_count}.")

    # 2. Ask user to pick the LABEL column
    while True:
        label_choice: str = input(f"LABEL/CLASS: Select column number for 'label' (1 - {total_columns_count}): ").strip()
        if label_choice.isdigit() and 1 <= int(label_choice) <= total_columns_count:
            chosen_label_col: str = available_cols[int(label_choice) - 1]
            break
        print(f"Invalid input. Please enter a number between 1 and {total_columns_count}.")

    # 3. Conflict Resolution: Check if existing columns are already named 'text' or 'label'
    displaced_renames: dict[str, str] = {}
    if "text" in available_cols and chosen_text_col != "text":
        old_text_new_name: str = input(
            "\n[CONFLICT] An existing column is already named 'text'. "
            "Rename old 'text' column to [Default: 'original_text']: "
        ).strip()
        displaced_renames["text"] = old_text_new_name if old_text_new_name else "original_text"

    if "label" in available_cols and chosen_label_col != "label":
        old_label_new_name: str = input(
            "\n[CONFLICT] An existing column is already named 'label'. "
            "Rename old 'label' column to [Default: 'original_label']: "
        ).strip()
        displaced_renames["label"] = old_label_new_name if old_label_new_name else "original_label"

    remediation_config["designated_text_column"] = chosen_text_col
    remediation_config["designated_label_column"] = chosen_label_col
    remediation_config["displaced_column_renames"] = displaced_renames

    print("\n[CONFIRMED]")
    print(f"  'text'  <--- '{chosen_text_col}'")
    print(f"  'label' <--- '{chosen_label_col}'")
    if displaced_renames:
        print(f"  Displaced renames: {displaced_renames}")

    # 4. Show distinct classes for the chosen LABEL column
    target_series: pd.Series = source_dataframe[chosen_label_col].dropna()
    distinct_label_value_counts: pd.Series = target_series.value_counts()
    unique_label_values_list: list[Any] = list(distinct_label_value_counts.index)
    total_non_null_rows: int = len(target_series)

    print(f"\nAll distinct classes in '{chosen_label_col}' ({len(unique_label_values_list)} total):")
    print(f"  {'#':<4} {'Class / Value':<35} {'Count':<15} {'Percentage'}")
    print("  " + "-" * 65)
    for label_idx, label_value in enumerate(unique_label_values_list, start=1):
        label_count: int = int(distinct_label_value_counts[label_value])
        label_pct: float = (
            round((label_count / total_non_null_rows * 100.0), 2)
            if total_non_null_rows > 0
            else 0.0
        )
        print(
            f"  [{label_idx:<2}] {repr(str(label_value))[:33]:<35} "
            f"{label_count:<15,d} "
            f"{label_pct}%"
        )

    # 5. Ask whether to binarize (0 and 1)

    # if len(unique_label_values_list) >= 2:
    #     binarize_choice: str = prompt_user_selection(
    #         f"\nConvert '{chosen_label_col}' into binary values (0 and 1)?",
    #         ["y", "n"],
    #         "n",
    #     )

    #     if binarize_choice == "y":
    #         while True:
    #             zero_class_input: str = input(
    #                 f"Enter number(s) of class(es) to map to 0 (comma-separated, e.g. 1 or 1,2): "
    #             ).strip()

    #             if not zero_class_input:
    #                 print("Input cannot be empty. Select at least one class index for Class 0.")
    #                 continue

    #             parsed_indices: list[int] = []
    #             is_valid: bool = True

    #             for token in zero_class_input.split(","):
    #                 cleaned: str = token.strip()
    #                 if cleaned.isdigit() and 1 <= int(cleaned) <= len(unique_label_values_list):
    #                     parsed_indices.append(int(cleaned))
    #                 else:
    #                     print(f"Index '{cleaned}' is invalid or out of range.")
    #                     is_valid = False
    #                     break

    #             if is_valid and parsed_indices:
    #                 selected_set: set[int] = set(parsed_indices)
    #                 if len(selected_set) == len(unique_label_values_list):
    #                     print("Cannot map ALL classes to 0. At least one must remain for Class 1.")
    #                     continue

    #                 zero_class_list: list[Any] = [
    #                     unique_label_values_list[idx - 1] for idx in selected_set
    #                 ]
    #                 one_class_list: list[Any] = [
    #                     val for val in unique_label_values_list if val not in zero_class_list
    #                 ]

    #                 print("\n" + "-" * 60)
    #                 print("[CONFIRMED BINARY CLASS MAPPING]")
    #                 print(f"  Target Column: '{chosen_label_col}'")
    #                 print(f"  Values mapped to 0 (Class 0): {zero_class_list}")
    #                 print(f"  Values mapped to 1 (Class 1): {one_class_list}")
    #                 print("-" * 60)

    #                 remediation_config["binary_class_conversion"] = {
    #                     "enabled": True,
    #                     "target_column_name": chosen_label_col,
    #                     "zero_class_values_list": zero_class_list,
    #                     "one_class_values_list": one_class_list,
    #                 }
    #                 break

    # # 5. Ask whether to binarize (0 and 1) with dual-direction aggregation support
    # if len(unique_label_values_list) >= 2:
    #     binarize_choice: str = prompt_user_selection(
    #         f"\nConvert '{chosen_label_col}' into binary values (0 and 1)?",
    #         ["y", "n"],
    #         "n",
    #     )

    #     if binarize_choice == "y":
    #         print("\nSelect Binary Aggregation Mode:")
    #         print("  [1] Designate Positive Class(es) -> Map selected to 1 (All unselected become 0)")
    #         print("  [0] Designate Negative Class(es) -> Map selected to 0 (All unselected become 1)")

    #         aggregation_target_mode: str = prompt_user_selection(
    #             "Choose which binary class you want to define",
    #             ["1", "0"],
    #             "1",
    #         )

    #         is_defining_positive_one: bool = (aggregation_target_mode == "1")
    #         prompt_label_name: str = "Class 1 (Positive)" if is_defining_positive_one else "Class 0 (Negative)"

    #         while True:
    #             user_indices_input_string: str = input(
    #                 f"Enter number(s) of class(es) to aggregate into {prompt_label_name} (comma-separated, e.g. 1 or 1,2): "
    #             ).strip()

    #             if not user_indices_input_string:
    #                 print(f"Input cannot be empty. Select at least one class index for {prompt_label_name}.")
    #                 continue

    #             parsed_selection_indices: list[int] = []
    #             input_validation_successful: bool = True

    #             for index_token in user_indices_input_string.split(","):
    #                 cleaned_token_string: str = index_token.strip()
    #                 if cleaned_token_string.isdigit() and 1 <= int(cleaned_token_string) <= len(unique_label_values_list):
    #                     parsed_selection_indices.append(int(cleaned_token_string))
    #                 else:
    #                     print(
    #                         f"Index '{cleaned_token_string}' is invalid. Must be an integer between 1 and {len(unique_label_values_list)}."
    #                     )
    #                     input_validation_successful = False
    #                     break

    #             if input_validation_successful and parsed_selection_indices:
    #                 selected_unique_indices_set: set[int] = set(parsed_selection_indices)
    #                 if len(selected_unique_indices_set) == len(unique_label_values_list):
    #                     print("Cannot map ALL available classes to one target. At least one class must remain for the opposite category.")
    #                     continue

    #                 selected_category_values_list: list[Any] = [
    #                     unique_label_values_list[class_index - 1] for class_index in selected_unique_indices_set
    #                 ]
    #                 unselected_category_values_list: list[Any] = [
    #                     category_value
    #                     for category_value in unique_label_values_list
    #                     if category_value not in selected_category_values_list
    #                 ]

    #                 if is_defining_positive_one:
    #                     aggregated_one_class_values_list: list[Any] = selected_category_values_list
    #                     aggregated_zero_class_values_list: list[Any] = unselected_category_values_list
    #                     default_fallback_binary_value: int = 0
    #                 else:
    #                     aggregated_zero_class_values_list = selected_category_values_list
    #                     aggregated_one_class_values_list = unselected_category_values_list
    #                     default_fallback_binary_value = 1

    #                 print("\n" + "-" * 60)
    #                 print("[CONFIRMED BINARY CLASS MAPPING]")
    #                 print(f"  Target Column:                   '{chosen_label_col}'")
    #                 print(f"  Values mapped to 0 (Negative):   {aggregated_zero_class_values_list}")
    #                 print(f"  Values mapped to 1 (Positive):   {aggregated_one_class_values_list}")
    #                 print(f"  Unmapped / Fallback Default:     {default_fallback_binary_value}")
    #                 print("-" * 60)

    #                 remediation_config["binary_class_conversion"] = {
    #                     "enabled": True,
    #                     "target_column_name": chosen_label_col,
    #                     "zero_class_values_list": aggregated_zero_class_values_list,
    #                     "one_class_values_list": aggregated_one_class_values_list,
    #                     "default_fallback_binary_value": default_fallback_binary_value,
    #                 }
    #                 break

    # 5. Multi-Class Dual Aggregation: Group classes into Class 0 AND Class 1
    if len(unique_label_values_list) >= 2:
        binarize_choice: str = prompt_user_selection(
            f"\nConvert '{chosen_label_col}' into binary values (0 and 1)?",
            ["y", "n"],
            "n",
        )

        if binarize_choice == "y":
            print("\n" + "=" * 70)
            print("  DUAL-CLASS AGGREGATION CONFIGURATION (0 AND 1)")
            print("=" * 70)

            # -----------------------------------------------------------------
            # STEP 4.5A: Select classes to aggregate into Class 0 (Negative)
            # -----------------------------------------------------------------
            print("\n--- STEP 5A: Define Class 0 (Negative) ---")
            print("Select one or more classes to aggregate into Class 0:")
            for class_idx, class_val in enumerate(unique_label_values_list, start=1):
                print(f"  [{class_idx:<2}] {repr(str(class_val))[:40]}")

            while True:
                zero_input_string: str = input(
                    "\nEnter class number(s) for Class 0 (comma-separated, e.g. 1 or 1,2): "
                ).strip()

                if not zero_input_string:
                    print("Input cannot be empty. You must select at least one class for Class 0.")
                    continue

                parsed_zero_indices: list[int] = []
                zero_input_is_valid: bool = True

                for token in zero_input_string.split(","):
                    cleaned_token: str = token.strip()
                    if cleaned_token.isdigit() and 1 <= int(cleaned_token) <= len(unique_label_values_list):
                        parsed_zero_indices.append(int(cleaned_token))
                    else:
                        print(f"Invalid index '{cleaned_token}'. Must be an integer between 1 and {len(unique_label_values_list)}.")
                        zero_input_is_valid = False
                        break

                if zero_input_is_valid and parsed_zero_indices:
                    selected_zero_indices_set: set[int] = set(parsed_zero_indices)
                    if len(selected_zero_indices_set) == len(unique_label_values_list):
                        print("Cannot assign ALL classes to Class 0. At least one class must remain for Class 1.")
                        continue

                    aggregated_zero_class_values_list: list[Any] = [
                        unique_label_values_list[idx - 1] for idx in selected_zero_indices_set
                    ]
                    break

            # -----------------------------------------------------------------
            # STEP 4.5B: Select classes to aggregate into Class 1 (Positive)
            # -----------------------------------------------------------------
            remaining_unassigned_values: list[Any] = [
                val for val in unique_label_values_list if val not in aggregated_zero_class_values_list
            ]

            print("\n--- STEP 5B: Define Class 1 (Positive) ---")
            print("Select one or more classes to aggregate into Class 1 from remaining classes:")
            for rem_idx, rem_val in enumerate(remaining_unassigned_values, start=1):
                print(f"  [{rem_idx:<2}] {repr(str(rem_val))[:40]}")

            while True:
                one_input_string: str = input(
                    "\nEnter class number(s) for Class 1 (comma-separated, e.g. 1 or 1,2): "
                ).strip()

                if not one_input_string:
                    print("Input cannot be empty. You must select at least one class for Class 1.")
                    continue

                parsed_one_indices: list[int] = []
                one_input_is_valid: bool = True

                for token in one_input_string.split(","):
                    cleaned_token = token.strip()
                    if cleaned_token.isdigit() and 1 <= int(cleaned_token) <= len(remaining_unassigned_values):
                        parsed_one_indices.append(int(cleaned_token))
                    else:
                        print(f"Invalid index '{cleaned_token}'. Must be an integer between 1 and {len(remaining_unassigned_values)}.")
                        one_input_is_valid = False
                        break

                if one_input_is_valid and parsed_one_indices:
                    selected_one_indices_set: set[int] = set(parsed_one_indices)
                    aggregated_one_class_values_list: list[Any] = [
                        remaining_unassigned_values[idx - 1] for idx in selected_one_indices_set
                    ]
                    break

            # -----------------------------------------------------------------
            # STEP 4.5C: Handle any leftover unassigned classes
            # -----------------------------------------------------------------
            leftover_unassigned_values: list[Any] = [
                val for val in remaining_unassigned_values if val not in aggregated_one_class_values_list
            ]

            unassigned_rows_handling_strategy: str = "drop"

            if leftover_unassigned_values:
                print(f"\n--- STEP 5C: Unassigned Classes Detected ({len(leftover_unassigned_values)}) ---")
                print(f"The following classes were not assigned to 0 or 1: {leftover_unassigned_values}")
                print("Choose how to handle rows with unassigned classes:")
                print("  [d] Drop rows containing unassigned classes [DEFAULT]")
                print("  [n] Set label to NaN (missing)")
                print("  [0] Map unassigned classes to Class 0")
                print("  [1] Map unassigned classes to Class 1")

                unassigned_choice: str = prompt_user_selection(
                    "Select action for unassigned classes",
                    ["d", "n", "0", "1"],
                    "d",
                )

                if unassigned_choice == "d":
                    unassigned_rows_handling_strategy = "drop"
                elif unassigned_choice == "n":
                    unassigned_rows_handling_strategy = "nan"
                elif unassigned_choice == "0":
                    aggregated_zero_class_values_list.extend(leftover_unassigned_values)
                    leftover_unassigned_values = []
                    unassigned_rows_handling_strategy = "none"
                elif unassigned_choice == "1":
                    aggregated_one_class_values_list.extend(leftover_unassigned_values)
                    leftover_unassigned_values = []
                    unassigned_rows_handling_strategy = "none"

            print("\n" + "-" * 70)
            print("[CONFIRMED DUAL BINARY AGGREGATION]")
            print(f"  Target Column:                         '{chosen_label_col}'")
            print(f"  Aggregated into Class 0 (Negative):     {aggregated_zero_class_values_list}")
            print(f"  Aggregated into Class 1 (Positive):     {aggregated_one_class_values_list}")
            if leftover_unassigned_values:
                print(f"  Unassigned Classes ({unassigned_rows_handling_strategy}):         {leftover_unassigned_values}")
            print("-" * 70)

            remediation_config["binary_class_conversion"] = {
                "enabled": True,
                "target_column_name": chosen_label_col,
                "zero_class_values_list": aggregated_zero_class_values_list,
                "one_class_values_list": aggregated_one_class_values_list,
                "unassigned_classes_list": leftover_unassigned_values,
                "unassigned_rows_handling_strategy": unassigned_rows_handling_strategy,
            }

    # =========================================================================
    # STEP 5: Missing Values (Null) Column Drop Threshold Filtering
    # =========================================================================
    print_section_divider("MISSING VALUES (NULL) AUDIT & FILTERING")
    total_dataset_rows_count: int = len(source_dataframe)
    columns_with_missing_data_summary: list[tuple[str, int, float, list[str]]] = []

    for column_name in source_dataframe.columns:
        null_count_in_column: int = int(source_dataframe[column_name].isna().sum())
        if null_count_in_column > 0:
            null_percentage_value: float = (
                round((null_count_in_column / total_dataset_rows_count * 100.0), 2)
                if total_dataset_rows_count > 0
                else 0.0
            )
            sample_non_null_values: list[str] = [
                str(value)[:30] for value in source_dataframe[column_name].dropna().iloc[:3]
            ]
            columns_with_missing_data_summary.append(
                (str(column_name), null_count_in_column, null_percentage_value, sample_non_null_values)
            )

    if not columns_with_missing_data_summary:
        print("Status: Clean. No missing (NaN / null) values detected in any column.")
        remediation_config["drop_null_threshold_columns_percentage"] = 100.0
    else:
        print(f"Detected {len(columns_with_missing_data_summary)} column(s) containing missing values:\n")
        print(f"  {'Column Name':<25} {'Missing Count':<18} {'Null %':<10} {'Sample Non-Null Data'}")
        print("  " + "-" * 80)
        for col_name, null_cnt, null_pct, sample_vals in columns_with_missing_data_summary:
            sample_representation_str: str = str(sample_vals) if sample_vals else "[Entirely Empty]"
            print(
                f"  {col_name[:24]:<25} "
                f"{f'{null_cnt:,} / {total_dataset_rows_count:,}':<18} "
                f"{f'{null_pct}%':<10} "
                f"{sample_representation_str}"
            )

        null_filter_choice: str = prompt_user_selection(
            "Would you like to drop columns that exceed a specific missing value percentage?",
            ["y", "n"],
            "n",
        )

        if null_filter_choice == "y":
            while True:
                threshold_input_str: str = input(
                    "Enter maximum allowable null percentage [0 - 100] (e.g., 50 will drop columns with >50% nulls): "
                ).strip()
                try:
                    threshold_float_val: float = float(threshold_input_str)
                    if 0.0 <= threshold_float_val <= 100.0:
                        columns_to_drop_preview: list[str] = [
                            col_name
                            for col_name, _, null_pct, _ in columns_with_missing_data_summary
                            if null_pct > threshold_float_val
                        ]
                        if columns_to_drop_preview:
                            print(
                                f"\n  [Impact Preview] Threshold {threshold_float_val}% will DROP "
                                f"{len(columns_to_drop_preview)} column(s):"
                            )
                            for dropped_col_name in columns_to_drop_preview:
                                print(f"    - '{dropped_col_name}'")
                        else:
                            print(
                                f"\n  [Impact Preview] Threshold {threshold_float_val}% will NOT drop any columns."
                            )

                        confirm_drop_choice: str = prompt_user_selection(
                            "Apply this column drop threshold?",
                            ["y", "n"],
                            "y",
                        )
                        if confirm_drop_choice == "y":
                            remediation_config["drop_null_threshold_columns_percentage"] = threshold_float_val
                            break
                    else:
                        print("Threshold must be between 0.0 and 100.0.")
                except ValueError:
                    print("Invalid input. Please enter a valid decimal number (e.g. 50 or 75.5).")

    # =========================================================================
    # STEP 6: Export Format & Destination Configuration
    # =========================================================================
    print_section_divider("EXPORT FORMAT & DESTINATION")
    target_export_format: str = prompt_user_selection(
        "Select output export format",
        ["csv", "jsonl", "json"],
        "jsonl",
    )
    remediation_config["export_format"] = target_export_format

    if target_export_format == "csv":
        delimiter_selection_choice: str = prompt_user_selection(
            "Select CSV output delimiter",
            ["comma", "tab", "semicolon", "pipe"],
            "comma",
        )
        delimiter_mapping_dict: dict[str, str] = {
            "comma": ",",
            "tab": "\t",
            "semicolon": ";",
            "pipe": "|",
        }
        remediation_config["export_delimiter"] = delimiter_mapping_dict[delimiter_selection_choice]

    while True:
        default_file_name: str = f"cleaned_dataset.{target_export_format}"
        target_path_input_str: str = input(
            f"Enter target destination file path (Default: {default_file_name}): "
        ).strip()
        if not target_path_input_str:
            target_path_input_str = default_file_name

        # Re-prompt if the destination file already exists on disk
        if os.path.exists(target_path_input_str):
            print(f"[WARNING] File '{target_path_input_str}' already exists. Please choose a different path or name.")
            continue

        try:
            target_directory_path: str = os.path.dirname(target_path_input_str)
            if target_directory_path and not os.path.exists(target_directory_path):
                os.makedirs(target_directory_path, exist_ok=True)
            remediation_config["target_output_file_path"] = target_path_input_str
            break
        except Exception as e:
            print(f"Invalid path or directory permission error: {e}")

    return remediation_config


def apply_dataset_cleaning_transformations(
    source_dataframe: pd.DataFrame,
    remediation_configuration: dict[str, Any],
) -> pd.DataFrame:
    """
    Applies the configured remediation transformations to produce a cleaned DataFrame.
    Executes deduplication, near-duplicate removals, mixed-type column coercions,
    multi-class to binary label consolidations, and null-heavy column drops.

    Parameters:
        source_dataframe (pd.DataFrame): The original input DataFrame.
        remediation_configuration (dict[str, Any]): The cleaning configuration dictionary
            containing all user-specified remediation decisions.

    Returns:
        pd.DataFrame: The transformed and cleaned DataFrame.
    """
    transformed_dataframe: pd.DataFrame = source_dataframe.copy()

    try:
        # =====================================================================
        # 1. Drop Exact Duplicate Rows
        # =====================================================================
        if remediation_configuration.get("drop_exact_duplicates", False):
            duplicate_retention_rule: str = remediation_configuration.get(
                "duplicate_retention_strategy", "first"
            )
            initial_rows_count: int = len(transformed_dataframe)

            if duplicate_retention_rule in ["first", "last"]:
                transformed_dataframe = transformed_dataframe.drop_duplicates(
                    keep=duplicate_retention_rule
                )
            elif duplicate_retention_rule == "none":
                transformed_dataframe = transformed_dataframe.drop_duplicates(keep=False)

            dropped_exact_count: int = initial_rows_count - len(transformed_dataframe)
            print(
                f"[REMEDIATION] Dropped {dropped_exact_count:,} duplicate rows using "
                f"strategy: '{duplicate_retention_rule}'."
            )

        # =====================================================================
        # 2. Drop Identified Near-Duplicate Rows
        # =====================================================================
        near_duplicate_indices_to_drop: set[Any] = remediation_configuration.get(
            "near_duplicate_indices_to_drop", set()
        )
        if near_duplicate_indices_to_drop:
            indices_present_in_dataframe: list[Any] = [
                row_index
                for row_index in near_duplicate_indices_to_drop
                if row_index in transformed_dataframe.index
            ]
            if indices_present_in_dataframe:
                transformed_dataframe = transformed_dataframe.drop(index=indices_present_in_dataframe)
                print(
                    f"[REMEDIATION] Dropped {len(indices_present_in_dataframe):,} row(s) "
                    f"selected from near-duplicate remediation."
                )

        # =====================================================================
        # 3. Remediate Mixed-Type Columns
        # =====================================================================
        mixed_type_actions_dict: dict[str, str] = remediation_configuration.get(
            "mixed_type_remediation_actions", {}
        )
        for column_name, conversion_action in mixed_type_actions_dict.items():
            if column_name not in transformed_dataframe.columns:
                continue

            if conversion_action == "numeric":
                transformed_dataframe[column_name] = pd.to_numeric(
                    transformed_dataframe[column_name], errors="coerce"
                )
                print(f"[REMEDIATION] Coerced column '{column_name}' to numeric (invalid values set to NaN).")
            elif conversion_action == "string":
                transformed_dataframe[column_name] = (
                    transformed_dataframe[column_name].astype(str).replace("nan", "")
                )
                print(f"[REMEDIATION] Coerced column '{column_name}' to uniform string representation.")

        # =====================================================================
        # 4. Multi-Class to Binary Class (0 and 1) Consolidation
        # =====================================================================
        # binary_conversion_settings: dict[str, Any] = remediation_configuration.get(
        #     "binary_class_conversion", {}
        # )
        # if binary_conversion_settings.get("enabled", False):
        #     target_column_name: str = binary_conversion_settings.get("target_column_name", "")

        #     if target_column_name in transformed_dataframe.columns:
        #         zero_class_values_set: set[Any] = set(
        #             binary_conversion_settings.get("zero_class_values_list", [])
        #         )
        #         one_class_values_set: set[Any] = set(
        #             binary_conversion_settings.get("one_class_values_list", [])
        #         )

        #         def convert_cell_value_to_binary(cell_value: Any) -> Any:
        #             # Preserve existing missing / NaN values without artificial imputation
        #             if pd.isna(cell_value):
        #                 return cell_value
        #             # Map designated baseline values to integer 0
        #             if cell_value in zero_class_values_set:
        #                 return 0
        #             # Map designated remaining values to integer 1
        #             if cell_value in one_class_values_set:
        #                 return 1
        #             # Fallback assignment for any unmapped non-null value
        #             return 1

        #         transformed_dataframe[target_column_name] = transformed_dataframe[
        #             target_column_name
        #         ].map(convert_cell_value_to_binary)

        #         # Count final binary distribution for console audit confirmation
        #         count_of_zero_values: int = int(
        #             (transformed_dataframe[target_column_name] == 0).sum()
        #         )
        #         count_of_one_values: int = int(
        #             (transformed_dataframe[target_column_name] == 1).sum()
        #         )
        #         print(
        #             f"[REMEDIATION] Converted column '{target_column_name}' to binary classes "
        #             f"(Class 0: {count_of_zero_values:,} rows, Class 1: {count_of_one_values:,} rows)."
        #         )

        # # =====================================================================
        # # 4. Multi-Class to Binary Class (0 and 1) Consolidation
        # # =====================================================================
        # binary_conversion_settings: dict[str, Any] = remediation_configuration.get(
        #     "binary_class_conversion", {}
        # )
        # if binary_conversion_settings.get("enabled", False):
        #     target_column_name: str = binary_conversion_settings.get("target_column_name", "")

        #     if target_column_name in transformed_dataframe.columns:
        #         zero_class_values_set: set[Any] = set(
        #             binary_conversion_settings.get("zero_class_values_list", [])
        #         )
        #         one_class_values_set: set[Any] = set(
        #             binary_conversion_settings.get("one_class_values_list", [])
        #         )
        #         default_fallback_binary_value: int = binary_conversion_settings.get(
        #             "default_fallback_binary_value", 0
        #         )

        #         def convert_cell_value_to_binary(cell_value: Any) -> Any:
        #             # Preserve existing missing / NaN values without artificial imputation
        #             if pd.isna(cell_value):
        #                 return cell_value
        #             # Map designated baseline values to integer 0 (Negative)
        #             if cell_value in zero_class_values_set:
        #                 return 0
        #             # Map designated positive values to integer 1 (Positive)
        #             if cell_value in one_class_values_set:
        #                 return 1
        #             # Fallback assignment for any unmapped non-null value
        #             return default_fallback_binary_value

        #         transformed_dataframe[target_column_name] = transformed_dataframe[
        #             target_column_name
        #         ].map(convert_cell_value_to_binary)

        #         # Count final binary distribution for console audit confirmation
        #         count_of_zero_values: int = int(
        #             (transformed_dataframe[target_column_name] == 0).sum()
        #         )
        #         count_of_one_values: int = int(
        #             (transformed_dataframe[target_column_name] == 1).sum()
        #         )
        #         print(
        #             f"[REMEDIATION] Converted column '{target_column_name}' to binary classes "
        #             f"(Class 0: {count_of_zero_values:,} rows, Class 1: {count_of_one_values:,} rows)."
        #         )


        # =====================================================================
        # 4. Multi-Class to Binary Class (0 and 1) Dual Aggregation Execution
        # =====================================================================
        binary_conversion_settings: dict[str, Any] = remediation_configuration.get(
            "binary_class_conversion", {}
        )
        if binary_conversion_settings.get("enabled", False):
            target_column_name: str = binary_conversion_settings.get("target_column_name", "")

            if target_column_name in transformed_dataframe.columns:
                zero_class_values_set: set[Any] = set(
                    binary_conversion_settings.get("zero_class_values_list", [])
                )
                one_class_values_set: set[Any] = set(
                    binary_conversion_settings.get("one_class_values_list", [])
                )
                unassigned_classes_set: set[Any] = set(
                    binary_conversion_settings.get("unassigned_classes_list", [])
                )
                unassigned_strategy: str = binary_conversion_settings.get(
                    "unassigned_rows_handling_strategy", "drop"
                )

                # Option 1: Drop rows matching unassigned classes before binarization
                if unassigned_strategy == "drop" and unassigned_classes_set:
                    initial_row_count: int = len(transformed_dataframe)
                    unassigned_mask: pd.Series = transformed_dataframe[target_column_name].isin(unassigned_classes_set)
                    transformed_dataframe = transformed_dataframe[~unassigned_mask]
                    dropped_unassigned_count: int = initial_row_count - len(transformed_dataframe)
                    print(
                        f"[REMEDIATION] Dropped {dropped_unassigned_count:,} row(s) containing unassigned classes: "
                        f"{list(unassigned_classes_set)}"
                    )

                def convert_cell_value_to_binary_aggregation(cell_value: Any) -> Any:
                    if pd.isna(cell_value):
                        return cell_value
                    if cell_value in zero_class_values_set:
                        return 0
                    if cell_value in one_class_values_set:
                        return 1
                    # Any remaining non-matching value (or unassigned with 'nan' strategy)
                    return float("nan")

                transformed_dataframe[target_column_name] = transformed_dataframe[
                    target_column_name
                ].map(convert_cell_value_to_binary_aggregation)

                count_of_zero_values: int = int((transformed_dataframe[target_column_name] == 0).sum())
                count_of_one_values: int = int((transformed_dataframe[target_column_name] == 1).sum())
                count_of_nan_values: int = int(transformed_dataframe[target_column_name].isna().sum())

                print(
                    f"[REMEDIATION] Successfully aggregated '{target_column_name}' into binary classes:\n"
                    f"  - Class 0 (Negative): {count_of_zero_values:,} rows\n"
                    f"  - Class 1 (Positive): {count_of_one_values:,} rows\n"
                    f"  - Missing / NaN:      {count_of_nan_values:,} rows"
                )

        # =====================================================================
        # 5. Filter Columns Exceeding Null Percentage Threshold
        # =====================================================================
        null_threshold_pct: float = remediation_configuration.get(
            "drop_null_threshold_columns_percentage", 100.0
        )
        if null_threshold_pct < 100.0 and len(transformed_dataframe) > 0:
            columns_to_drop_list: list[str] = []
            for column_name in transformed_dataframe.columns:
                column_null_percentage: float = (
                    transformed_dataframe[column_name].isna().sum() / len(transformed_dataframe)
                ) * 100.0
                if column_null_percentage > null_threshold_pct:
                    columns_to_drop_list.append(str(column_name))

            if columns_to_drop_list:
                transformed_dataframe.drop(columns=columns_to_drop_list, inplace=True)
                print(
                    f"[REMEDIATION] Dropped {len(columns_to_drop_list)} column(s) exceeding "
                    f"{null_threshold_pct}% null threshold: {columns_to_drop_list}"
                )

        # =====================================================================
        # 6. Rename user-selected columns to 'text' and 'label'
        # =====================================================================
        # Step A: Free up 'text'/'label' names if old columns held them
        displaced_map: dict[str, str] = remediation_configuration.get("displaced_column_renames", {})
        if displaced_map:
            transformed_dataframe.rename(columns=displaced_map, inplace=True)

        # Step B: Rename user-selected columns to 'text' and 'label'
        target_text_col: str | None = remediation_configuration.get("designated_text_column")
        target_label_col: str | None = remediation_configuration.get("designated_label_column")

        rename_mapping: dict[str, str] = {}
        if target_text_col and target_text_col in transformed_dataframe.columns and target_text_col != "text":
            rename_mapping[target_text_col] = "text"

        if target_label_col and target_label_col in transformed_dataframe.columns and target_label_col != "label":
            rename_mapping[target_label_col] = "label"

        if rename_mapping:
            transformed_dataframe.rename(columns=rename_mapping, inplace=True)
            print(f"[REMEDIATION] Output columns renamed: {rename_mapping}")

        return transformed_dataframe

    except Exception:
        sys.stderr.write(
            f"[FATAL ERROR] Dataset transformation failed with an unhandled exception.\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        return transformed_dataframe


def export_processed_dataset_file(
    processed_dataframe: pd.DataFrame,
    target_file_path: str,
    export_format: str = "jsonl",
    delimiter_character: str = ",",
) -> None:
    """
    Serializes and writes the processed DataFrame to disk in CSV or JSON/JSONL format.
    Sanitizes all string/object fields by collapsing internal newlines and carriage returns
    into spaces, ensuring clean single-line records for JSONL ingestion.

    Parameters:
        processed_dataframe (pd.DataFrame): DataFrame to serialize.
        target_file_path (str): File destination path.
        export_format (str): Output format ('csv', 'json', or 'jsonl').
        delimiter_character (str): Delimiter character for CSV output.

    Raises:
        IOError / Exception: If serialization or writing fails.
    """
    try:
        # Work on a copy to avoid mutating the in-memory dataframe
        export_df: pd.DataFrame = processed_dataframe.copy()

        # Sanitize all string/object columns: collapse \r\n, \n, and \r into a single space
        for column_name in export_df.columns:
            if export_df[column_name].dtype == "object":
                export_df[column_name] = export_df[column_name].map(
                    lambda val: re.sub(r"[\r\n]+", " ", str(val)).strip() if pd.notna(val) else val
                )

        format_lower: str = export_format.lower()
        if format_lower == "csv":
            export_df.to_csv(
                target_file_path,
                sep=delimiter_character,
                index=False,
                encoding="utf-8",
            )
        elif format_lower in ["json", "jsonl"]:
            is_jsonl: bool = target_file_path.endswith(".jsonl") or format_lower == "jsonl"

            export_df.to_json(
                target_file_path,
                orient="records",
                lines=is_jsonl,                 # True outputs 1 JSON object per line
                indent=None if is_jsonl else 2, # Must be None for strict JSONL
                date_format="iso",
                force_ascii=False,              # Preserves UTF-8 characters without \uXXXX escaping
            )
        else:
            raise ValueError(
                f"Unsupported export format '{export_format}'. Expected 'csv', 'json', or 'jsonl'."
            )

        print(f"\n[SUCCESS] Successfully exported {len(export_df):,} records to: {target_file_path}")

    except Exception:
        sys.stderr.write(
            f"[FATAL ERROR] Failed to export processed dataset to: {target_file_path}\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        raise


def prompt_near_duplicate_group_resolution(
    source_dataframe: pd.DataFrame,
    near_duplicate_records: list[dict[str, Any]],
    evaluated_text_column_name: str | None = None,
) -> set[Any]:
    """
    Presents an interactive terminal workflow allowing the user to resolve
    near-duplicate groups either via a global bulk rule across all groups
    or via individual group-by-group manual review.

    Parameters:
        source_dataframe (pd.DataFrame): The DataFrame being audited, used to retrieve
            row text previews and maintain file order.
        near_duplicate_records (list[dict[str, Any]]): List of pairwise near-duplicate
            records from the distance audit.
        evaluated_text_column_name (str | None): Optional specific text column name
            to preview during group inspection. If None, the entire row is summarized.

    Returns:
        set[Any]: Set of DataFrame row index labels designated for deletion.
    """
    row_indices_designated_for_removal: set[Any] = set()

    if not near_duplicate_records:
        return row_indices_designated_for_removal

    try:
        # Cluster pairwise records into connected groups ordered by file row position
        connected_duplicate_groups: list[dict[str, Any]] = (
            cluster_near_duplicate_records_into_connected_groups(
                near_duplicate_records=near_duplicate_records,
                source_dataframe=source_dataframe,
            )
        )

        total_detected_groups_count: int = len(connected_duplicate_groups)
        total_rows_involved_count: int = sum(
            group["member_row_count"] for group in connected_duplicate_groups
        )

        print_section_divider("NEAR-DUPLICATE GROUP REMEDIATION")
        print(
            f"Detected {total_detected_groups_count:,} duplicate group(s) "
            f"spanning {total_rows_involved_count:,} total rows.\n"
        )

        # =====================================================================
        # LEVEL 1: Top-Level Decision for ALL Groups
        # =====================================================================
        print("How would you like to handle these groups?")
        print("  [1] Bulk Action:       Apply one rule to ALL groups automatically")
        print("  [2] Individual Action: Review and resolve each group one by one")
        print("  [3] Skip:              Do not drop any near-duplicates (keep everything)")

        top_level_workflow_choice: str = prompt_user_selection(
            prompt_text="Enter selection for duplicate groups",
            valid_choices=["1", "2", "3"],
            default_choice="1",
        )

        if top_level_workflow_choice == "3":
            print("[INFO] Skipping near-duplicate remediation. All rows retained.")
            return row_indices_designated_for_removal

        # =====================================================================
        # LEVEL 1 -> PATH A: Bulk Action Across All Groups
        # =====================================================================
        if top_level_workflow_choice == "1":
            print(f"\nSelect global resolution rule for all {total_detected_groups_count:,} groups:")
            print("  [a] Keep First -> In every group, keep the earliest row in the file; drop subsequent duplicates.")
            print("  [b] Keep Last  -> In every group, keep the latest row in the file; drop earlier duplicates.")
            print("  [c] Drop All   -> Delete every row involved in any duplicate group.")

            global_rule_choice: str = prompt_user_selection(
                prompt_text="Choose global rule for all groups",
                valid_choices=["a", "b", "c"],
                default_choice="a",
            )

            for group_record in connected_duplicate_groups:
                member_indices: list[Any] = group_record["member_row_indices_in_dataset_order"]

                if global_rule_choice == "a":
                    # Keep member_indices[0] (earliest row); drop all remaining members
                    for subsequent_row_index in member_indices[1:]:
                        row_indices_designated_for_removal.add(subsequent_row_index)

                elif global_rule_choice == "b":
                    # Keep member_indices[-1] (latest row); drop all preceding members
                    for preceding_row_index in member_indices[:-1]:
                        row_indices_designated_for_removal.add(preceding_row_index)

                elif global_rule_choice == "c":
                    # Drop every member of the group
                    for row_index in member_indices:
                        row_indices_designated_for_removal.add(row_index)

            action_description: str = (
                "kept earliest row per group" if global_rule_choice == "a"
                else "kept latest row per group" if global_rule_choice == "b"
                else "dropped all group members"
            )
            print(
                f"\n[BULK RESOLVE COMPLETE] Applied global rule ({action_description}). "
                f"Designated {len(row_indices_designated_for_removal):,} row(s) for removal."
            )
            return row_indices_designated_for_removal

        # =====================================================================
        # LEVEL 1 -> PATH B: Individual Group-by-Group Manual Review
        # =====================================================================
        if top_level_workflow_choice == "2":
            print("\n" + "=" * 80)
            print("  INDIVIDUAL GROUP-BY-GROUP REVIEW")
            print("=" * 80)

            for group_index, group_record in enumerate(connected_duplicate_groups, start=1):
                member_indices = group_record["member_row_indices_in_dataset_order"]
                member_count = group_record["member_row_count"]

                print(f"\n--- Group {group_index} of {total_detected_groups_count} ({member_count} rows) ---")

                # Display each row in the group with its dataset row index and text preview
                for display_position, row_index_label in enumerate(member_indices, start=1):
                    if evaluated_text_column_name and evaluated_text_column_name in source_dataframe.columns:
                        preview_text_snippet: str = str(
                            source_dataframe.loc[row_index_label, evaluated_text_column_name]
                        )[:65]
                    else:
                        preview_text_snippet = str(
                            source_dataframe.loc[row_index_label].to_dict()
                        )[:65]

                    position_descriptor: str = (
                        " [Earliest in file]" if display_position == 1
                        else " [Latest in file]" if display_position == member_count
                        else ""
                    )
                    print(
                        f"  [{display_position}] Row Index {row_index_label:<8}: "
                        f"\"{preview_text_snippet}\"{position_descriptor}"
                    )

                valid_selection_choices: list[str] = [
                    str(num) for num in range(1, member_count + 1)
                ] + ["d", "k"]

                print("\nAction for this group:")
                print(f"  [1-{member_count}] Keep only that specific row (drop all others in this group)")
                print("  [d]   Drop ALL rows in this group")
                print("  [k]   Keep ALL rows in this group (skip/retain all)")

                group_action_choice: str = prompt_user_selection(
                    prompt_text=f"Select action for Group #{group_index}",
                    valid_choices=valid_selection_choices,
                    default_choice="1",
                )

                if group_action_choice.isdigit():
                    selected_keep_position: int = int(group_action_choice) - 1
                    preserved_row_index: Any = member_indices[selected_keep_position]
                    for drop_candidate_index in member_indices:
                        if drop_candidate_index != preserved_row_index:
                            row_indices_designated_for_removal.add(drop_candidate_index)

                elif group_action_choice == "d":
                    for drop_candidate_index in member_indices:
                        row_indices_designated_for_removal.add(drop_candidate_index)

                elif group_action_choice == "k":
                    pass

            print(
                f"\n[MANUAL REVIEW COMPLETE] Group review finished. "
                f"Designated {len(row_indices_designated_for_removal):,} row(s) for removal."
            )
            return row_indices_designated_for_removal

        return row_indices_designated_for_removal

    except Exception:
        sys.stderr.write(
            f"[ERROR] An unexpected error occurred during near-duplicate group resolution wizard.\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        return row_indices_designated_for_removal

# =====================================================================
# SECTION 8: CLI ROUTER & CONTROLLER ORCHESTRATION
# =====================================================================


def parse_command_line_arguments() -> argparse.Namespace:
    """Configures and parses command-line interface arguments."""
    parser = argparse.ArgumentParser(
        description="Dataset File Checker, Auditor, and Cleaning Tool."
    )
    parser.add_argument("-f", "--file", type=str, help="Path to single dataset file to audit and clean.")
    parser.add_argument("--train", type=str, help="Path to reference training partition file (Part B audit).")
    parser.add_argument("--test", type=str, help="Path to evaluation testing partition file (Part B audit).")
    parser.add_argument("--target-column", type=str, default=None, help="Target label column name in train/test audit.")
    parser.add_argument("-o", "--out", type=str, default=None, help="Destination output file path for cleaned data.")
    parser.add_argument(
        "--format",
        type=str,
        choices=["csv", "json", "jsonl"],
        default="jsonl",
        help="Target export format.",
    )
    parser.add_argument("--delimiter", type=str, default=None, help="Explicit delimiter override for CSV input.")
    parser.add_argument("--similarity-threshold", type=float, default=0.85, help="Fuzzy near-duplicate similarity threshold (0.0 to 1.0).")
    parser.add_argument("--non-interactive", action="store_true", help="Run audit only without interactive remediation prompts.")
    parser.add_argument(
            "--skip-near-duplicates",
            action="store_true",
            help="Disable the Levenshtein near-duplicate evaluation entirely.",
        )
    parser.add_argument(
            "--workers",
            type=int,
            default=None,
            help="Worker process count for parallel duplicate scanning (default: CPU cores minus one).",
        )

    return parser.parse_args()


def interactive_wizard_mode_selection() -> tuple[str, dict[str, Any]]:
    """Guides the user through mode selection if no CLI flags were provided."""
    print_section_divider("DATASET AUDITOR & CHECKER - INTERACTIVE MODE")
    print("Select an execution mode:")
    print("  [1] Single Dataset Ingestion, Audit & Interactive Cleaning")
    print("  [2] Train/Test Partition Integrity & Leakage Verification (Read-Only)")

    mode_choice = prompt_user_selection("Enter mode", ["1", "2"], "1")

    options_dict: dict[str, Any] = {}
    if mode_choice == "1":
        while True:
            file_path_input = input("Enter path to dataset file (.csv, .tsv, .json, .jsonl): ").strip()
            if os.path.exists(file_path_input):
                options_dict["file_path"] = file_path_input
                break
            print(f"File not found: '{file_path_input}'. Please enter a valid path.")
        return "single", options_dict
    else:
        while True:
            train_path_input = input("Enter path to TRAIN dataset file: ").strip()
            if os.path.exists(train_path_input):
                options_dict["train_path"] = train_path_input
                break
            print(f"File not found: '{train_path_input}'. Please enter a valid path.")

        while True:
            test_path_input = input("Enter path to TEST dataset file: ").strip()
            if os.path.exists(test_path_input):
                options_dict["test_path"] = test_path_input
                break
            print(f"File not found: '{test_path_input}'. Please enter a valid path.")

        target_col = input("Enter target label column name (or press Enter to skip): ").strip()
        options_dict["target_column"] = target_col if target_col else None
        return "train_test", options_dict


def main_execution_controller() -> None:
    """Main orchestration controller governing application flow."""
    cli_arguments: argparse.Namespace = parse_command_line_arguments()

    # Determine execution workflow
    if cli_arguments.train and cli_arguments.test:
        # 1. CLI-driven Train/Test Audit
        try:
            print(f"[INFO] Ingesting training partition: {cli_arguments.train}")
            train_df, _ = read_source_dataset_file(cli_arguments.train, cli_arguments.delimiter)
            print(f"[INFO] Ingesting testing partition: {cli_arguments.test}")
            test_df, _ = read_source_dataset_file(cli_arguments.test, cli_arguments.delimiter)

            audit_results = audit_train_test_split_integrity(train_df, test_df, cli_arguments.target_column)
            display_train_test_audit_report(cli_arguments.train, cli_arguments.test, audit_results)
        except Exception as error_exception:
            sys.stderr.write(f"[FATAL CONTROLLER ERROR] Train/test audit aborted: {error_exception}\n")
            sys.exit(1)

    elif cli_arguments.file:
        # 2. CLI-driven Single Dataset Audit & Optional Remediation
        try:
            print(f"[INFO] Ingesting dataset: {cli_arguments.file}")
            source_df, malformed_rows = read_source_dataset_file(cli_arguments.file, cli_arguments.delimiter)

            mixed_types = detect_mixed_data_types_in_dataframe(source_df)
            describe_df, extended_metrics = generate_comprehensive_descriptive_statistics(source_df)
            exact_dupes = identify_exact_duplicate_rows(source_df)

            if not cli_arguments.skip_near_duplicates:
                near_dupes = identify_near_duplicate_rows(
                    source_df,
                    similarity_threshold=cli_arguments.similarity_threshold,
                    maximum_allowable_edit_distance=2,
                )
            else:
                near_dupes = []

            display_single_dataset_audit_report(
                source_file_path=cli_arguments.file,
                source_dataframe=source_df,
                malformed_rows_list=malformed_rows,
                mixed_types_report=mixed_types,
                standard_describe_dataframe=describe_df,
                extended_metrics_report=extended_metrics,
                exact_duplicates_report=exact_dupes,
                near_duplicates_report=near_dupes,
            )

            if not cli_arguments.non_interactive:
                remediation_config = prompt_interactive_cleaning_configuration(
                    source_dataframe=source_df,
                    exact_duplicates_report=exact_dupes,
                    mixed_types_report=mixed_types,
                    near_duplicates_report=near_dupes,
                )
                cleaned_df = apply_dataset_cleaning_transformations(source_df, remediation_config)
                export_processed_dataset_file(
                    cleaned_df,
                    remediation_config["target_output_file_path"],
                    remediation_config["export_format"],
                    remediation_config.get("export_delimiter", ","),
                )
        except Exception as error_exception:
            sys.stderr.write(f"[FATAL CONTROLLER ERROR] Dataset audit aborted: {error_exception}\n")
            sys.exit(1)

    else:
        # 3. Interactive Wizard Flow (No CLI arguments provided)
        mode, options = interactive_wizard_mode_selection()

        if mode == "train_test":
            try:
                print(f"\n[INFO] Ingesting training partition: {options['train_path']}")
                train_df, _ = read_source_dataset_file(options["train_path"])
                print(f"[INFO] Ingesting testing partition: {options['test_path']}")
                test_df, _ = read_source_dataset_file(options["test_path"])

                audit_results = audit_train_test_split_integrity(train_df, test_df, options["target_column"])
                display_train_test_audit_report(options["train_path"], options["test_path"], audit_results)
            except Exception as error_exception:
                sys.stderr.write(f"[FATAL CONTROLLER ERROR] Train/test audit aborted: {error_exception}\n")
                sys.exit(1)

        elif mode == "single":
            try:
                file_path = options["file_path"]
                print(f"\n[INFO] Ingesting dataset: {file_path}")
                source_df, malformed_rows = read_source_dataset_file(file_path)

                mixed_types = detect_mixed_data_types_in_dataframe(source_df)
                describe_df, extended_metrics = generate_comprehensive_descriptive_statistics(source_df)
                exact_dupes = identify_exact_duplicate_rows(source_df)
                # Interactive prompt for near-duplicate strictness or skip
                (
                    run_near_dupe_check,
                    similarity_threshold,
                    max_edits,
                    target_text_col,
                ) = prompt_near_duplicate_configuration(source_df)

                if run_near_dupe_check:
                    print("\n[INFO] Calculating Levenshtein distance on target text:")
                    print("\n...this might take a while...")
                    target_cols_list = [target_text_col] if target_text_col else None
                    near_dupes = identify_near_duplicate_rows(
                        source_df,
                        target_columns_subset=target_cols_list,
                        similarity_threshold=similarity_threshold,
                        maximum_allowable_edit_distance=max_edits,
                    )
                else:
                    near_dupes = []


                display_single_dataset_audit_report(
                    source_file_path=file_path,
                    source_dataframe=source_df,
                    malformed_rows_list=malformed_rows,
                    mixed_types_report=mixed_types,
                    standard_describe_dataframe=describe_df,
                    extended_metrics_report=extended_metrics,
                    exact_duplicates_report=exact_dupes,
                    near_duplicates_report=near_dupes,
                )

                remediation_config = prompt_interactive_cleaning_configuration(
                    source_dataframe=source_df,
                    exact_duplicates_report=exact_dupes,
                    mixed_types_report=mixed_types,
                    near_duplicates_report=near_dupes,
                )
                cleaned_df = apply_dataset_cleaning_transformations(source_df, remediation_config)
                export_processed_dataset_file(
                    cleaned_df,
                    remediation_config["target_output_file_path"],
                    remediation_config["export_format"],
                    remediation_config.get("export_delimiter", ","),
                )
            except Exception as error_exception:
                sys.stderr.write(f"[FATAL CONTROLLER ERROR] Dataset audit aborted: {error_exception}\n")
                sys.exit(1)


if __name__ == "__main__":
    main_execution_controller()
