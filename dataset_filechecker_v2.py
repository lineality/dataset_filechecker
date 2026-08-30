
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
    *   Compares candidate rows using Levenshtein distance / `difflib.SequenceMatcher.ratio()` against a user-configurable similarity threshold (e.g., similarity $\ge 0.85$).
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
import csv
import difflib
import json
import os
import re
import sys
import traceback
from collections import defaultdict
from collections.abc import Iterator, Sequence
from typing import Any
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

    except Exception as error_exception:
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

    except Exception as error_exception:
        sys.stderr.write(
            f"[FATAL ERROR] Ingestion failed for source dataset: {source_file_path}\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        raise error_exception

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


def identify_exact_duplicate_rows(
    source_dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Identifies completely identical rows across all columns using vectorized
    64-bit integer hashing for scale and efficiency.

    Parameters:
        source_dataframe (pd.DataFrame): The DataFrame to evaluate.

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
        # Generate 64-bit deterministic hash array across all columns
        row_hashes_series: pd.Series = pd.util.hash_pandas_object(source_dataframe, index=False)

        # Identify duplicate hashes
        hash_frequency_counts: pd.Series = row_hashes_series.value_counts()
        duplicate_hashes: set[int] = set(hash_frequency_counts[hash_frequency_counts > 1].index)

        duplicate_index_clusters: list[list[int]] = []
        total_duplicate_rows_count: int = 0

        # Group indices by identical hash value
        for duplicate_hash_value in duplicate_hashes:
            matching_indices: list[int] = source_dataframe.index[
                row_hashes_series == duplicate_hash_value
            ].tolist()
            duplicate_index_clusters.append(matching_indices)
            total_duplicate_rows_count += len(matching_indices)

        return {
            "total_duplicate_rows_count": total_duplicate_rows_count,
            "duplicate_cluster_count": len(duplicate_index_clusters),
            "duplicate_index_clusters": duplicate_index_clusters,
        }

    except Exception as error_exception:
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


def identify_near_duplicate_rows(
    source_dataframe: pd.DataFrame,
    target_columns_subset: list[str] | None = None,
    similarity_threshold: float = 0.98,
    maximum_allowable_edit_distance: int = 2,
    minimum_character_length: int = 15,
    maximum_candidate_comparisons: int | None = None,
) -> list[dict[str, Any]]:
    """
    Identifies near-duplicate text records by evaluating exact Levenshtein edit
    distance specifically on designated free-form text column(s). Applies both
    a proportional similarity threshold and an absolute edit distance ceiling.
    Includes a real-time 10% status counter to track row comparison progress.

    Parameters:
        source_dataframe (pd.DataFrame): The DataFrame to audit.
        target_columns_subset (list[str] | None): Specific text columns to evaluate.
            If None, candidate text columns are automatically detected.
        similarity_threshold (float): Minimum normalized similarity score [0.0 - 1.0].
        maximum_allowable_edit_distance (int): Maximum absolute character edits allowed.
        minimum_character_length (int): Minimum normalized character length required
            to be evaluated.
        maximum_candidate_comparisons (int | None): Safety ceiling on pairwise comparisons.

    Returns:
        list[dict[str, Any]]: Detailed records of near-duplicate row pairs:
            {
                'row_index_first': Any,
                'row_index_second': Any,
                'evaluated_columns': list[str],
                'levenshtein_distance': int,
                'similarity_score': float,
                'raw_text_first': str,
                'raw_text_second': str,
                'normalized_string_first': str,
                'normalized_string_second': str,
                'differing_fields_breakdown': dict[str, tuple[str, str]],
                'matching_fields_list': list[str]
            }
    """
    near_duplicate_records: list[dict[str, Any]] = []

    if source_dataframe.empty or len(source_dataframe) < 2:
        return near_duplicate_records

    try:
        # Determine specific text columns to evaluate
        evaluated_text_columns: list[str] = (
            target_columns_subset
            if target_columns_subset is not None and len(target_columns_subset) > 0
            else detect_candidate_text_columns(source_dataframe)
        )

        if not evaluated_text_columns:
            sys.stderr.write("[WARNING] No text columns identified for near-duplicate evaluation.\n")
            return near_duplicate_records

        total_row_count: int = len(source_dataframe)

        # Normalize target text column(s) per row
        normalized_row_text_list: list[str] = []
        raw_text_preview_list: list[str] = []

        for _, row_series in source_dataframe[evaluated_text_columns].iterrows():
            raw_text_combined: str = " ".join(
                str(row_series[col]) for col in evaluated_text_columns if pd.notna(row_series[col])
            )
            normalized_text: str = normalize_text_content_alphanumeric_lowercase(raw_text_combined)

            normalized_row_text_list.append(normalized_text)
            raw_text_preview_list.append(raw_text_combined)

        total_comparisons_performed: int = 0

        # Calculate status counter step size (10% intervals, minimum 1 row to prevent division by zero)
        progress_reporting_chunk_size: int = max(1, total_row_count // 10)
        print(
            f"  [STATUS] Beginning Levenshtein distance check across {total_row_count:,} rows "
            f"(reporting progress every ~{progress_reporting_chunk_size:,} rows)...\n",
            flush=True,
        )

        # Pairwise Levenshtein comparison on isolated text
        for index_a in range(total_row_count):
            string_a: str = normalized_row_text_list[index_a]
            length_a: int = len(string_a)

            # Check if current outer row index hits a 10% progress reporting milestone
            current_rows_evaluated_count: int = index_a + 1
            if (
                current_rows_evaluated_count % progress_reporting_chunk_size == 0
                or current_rows_evaluated_count == total_row_count
            ):
                progress_completion_percentage: float = round(
                    (current_rows_evaluated_count / total_row_count) * 100.0, 1
                )
                print(
                    f"  [STATUS] Scanned {current_rows_evaluated_count:,} / {total_row_count:,} rows "
                    f"({progress_completion_percentage}%) | Found {len(near_duplicate_records):,} candidate near-duplicate pair(s)...",
                    flush=True,
                )

            if length_a < minimum_character_length:
                continue

            for index_b in range(index_a + 1, total_row_count):
                string_b: str = normalized_row_text_list[index_b]
                length_b: int = len(string_b)

                if length_b < minimum_character_length:
                    continue

                # Skip identical normalized text (handled by exact duplicate check)
                if string_a == string_b:
                    continue

                maximum_length: int = max(length_a, length_b)
                ratio_based_edits: int = int(maximum_length * (1.0 - similarity_threshold))
                # Enforce both proportional similarity and absolute edit cap
                effective_maximum_edits: int = min(ratio_based_edits, maximum_allowable_edit_distance)

                if effective_maximum_edits == 0:
                    continue

                total_comparisons_performed += 1
                if (
                    maximum_candidate_comparisons is not None
                    and total_comparisons_performed > maximum_candidate_comparisons
                ):
                    break

                edit_distance: int = calculate_exact_levenshtein_distance(
                    first_string=string_a,
                    second_string=string_b,
                    maximum_distance_cutoff=effective_maximum_edits,
                )

                if edit_distance <= effective_maximum_edits:
                    similarity_ratio: float = 1.0 - (edit_distance / maximum_length)

                    actual_row_label_a: Any = source_dataframe.index[index_a]
                    actual_row_label_b: Any = source_dataframe.index[index_b]

                    row_series_a: pd.Series = source_dataframe.loc[actual_row_label_a]
                    row_series_b: pd.Series = source_dataframe.loc[actual_row_label_b]

                    differing_fields: dict[str, tuple[str, str]] = {}
                    matching_fields: list[str] = []

                    for column_name in source_dataframe.columns:
                        val_a: str = str(row_series_a[column_name])
                        val_b: str = str(row_series_b[column_name])

                        if val_a == val_b:
                            matching_fields.append(str(column_name))
                        else:
                            differing_fields[str(column_name)] = (val_a, val_b)

                    near_duplicate_records.append(
                        {
                            "row_index_first": actual_row_label_a,
                            "row_index_second": actual_row_label_b,
                            "evaluated_columns": evaluated_text_columns,
                            "levenshtein_distance": edit_distance,
                            "similarity_score": round(similarity_ratio, 4),
                            "raw_text_first": raw_text_preview_list[index_a],
                            "raw_text_second": raw_text_preview_list[index_b],
                            "normalized_string_first": string_a,
                            "normalized_string_second": string_b,
                            "differing_fields_breakdown": differing_fields,
                            "matching_fields_list": matching_fields,
                        }
                    )

            if (
                maximum_candidate_comparisons is not None
                and total_comparisons_performed > maximum_candidate_comparisons
            ):
                break

        print(
            f"\n  [COMPLETED] Levenshtein check finished. Total pairs flagged: {len(near_duplicate_records):,}\n",
            flush=True,
        )
        near_duplicate_records.sort(key=lambda record: record["similarity_score"], reverse=True)
        return near_duplicate_records

    except Exception as error_exception:
        sys.stderr.write(
            f"[ERROR] An unexpected failure occurred during text-level Levenshtein audit.\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        return near_duplicate_records

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

    except Exception as error_exception:
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
            f"\nSelect column number to evaluate (1 - {len(all_column_names)}) (Default: [{default_column_index}] {all_column_names[default_column_index - 1]}): "
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

    # =========================================================================
    # STEP 2: Near-Duplicate Row Resolution
    # =========================================================================
    if near_duplicates_report and len(near_duplicates_report) > 0:
        total_near_duplicate_pairs_count: int = len(near_duplicates_report)
        print(f"\n[NEAR-DUPLICATE REMEDIATION] Detected {total_near_duplicate_pairs_count} near-duplicate pair(s).")

        auto_resolve_choice: str = prompt_user_selection(
            "Auto resolve (keep one of each), or manual handling?",
            ["y", "n"],
            "n",
        )

        indices_to_drop_set: set[Any] = set()

        if auto_resolve_choice == "y":
            for pair_record in near_duplicates_report:
                secondary_row_index: Any = pair_record["row_index_second"]
                indices_to_drop_set.add(secondary_row_index)
            print(f"[AUTO RESOLVE] Marked {len(indices_to_drop_set)} secondary row(s) for removal.")
        else:
            print("\nManual Pair-by-Pair Resolution:")
            for pair_index, pair_record in enumerate(near_duplicates_report, start=1):
                row_index_first: Any = pair_record["row_index_first"]
                row_index_second: Any = pair_record["row_index_second"]
                similarity_percentage: float = round(pair_record["similarity_score"] * 100.0, 2)
                edit_distance_count: int = pair_record["levenshtein_distance"]

                print(
                    f"\n  Pair #{pair_index}: Row [{row_index_first}] <---> Row [{row_index_second}] "
                    f"(Similarity: {similarity_percentage}%, Edits: {edit_distance_count})"
                )
                print(f"    [a] Keep Row [{row_index_first}] (drop Row [{row_index_second}])")
                print(f"    [b] Keep Row [{row_index_second}] (drop Row [{row_index_first}])")
                print("    [d] Drop both rows")
                print("    [k] Keep both rows (skip / ignore this pair)")

                pair_action_choice: str = prompt_user_selection(
                    f"Action for Pair #{pair_index}",
                    ["a", "b", "d", "k"],
                    "k",
                )

                if pair_action_choice == "a":
                    indices_to_drop_set.add(row_index_second)
                elif pair_action_choice == "b":
                    indices_to_drop_set.add(row_index_first)
                elif pair_action_choice == "d":
                    indices_to_drop_set.add(row_index_first)
                    indices_to_drop_set.add(row_index_second)
                elif pair_action_choice == "k":
                    pass

        remediation_config["near_duplicate_indices_to_drop"] = indices_to_drop_set

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

    print(f"\n[CONFIRMED]")
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
    if len(unique_label_values_list) >= 2:
        binarize_choice: str = prompt_user_selection(
            f"\nConvert '{chosen_label_col}' into binary values (0 and 1)?",
            ["y", "n"],
            "n",
        )

        if binarize_choice == "y":
            while True:
                zero_class_input: str = input(
                    f"Enter number(s) of class(es) to map to 0 (comma-separated, e.g. 1 or 1,2): "
                ).strip()

                if not zero_class_input:
                    print("Input cannot be empty. Select at least one class index for Class 0.")
                    continue

                parsed_indices: list[int] = []
                is_valid: bool = True

                for token in zero_class_input.split(","):
                    cleaned: str = token.strip()
                    if cleaned.isdigit() and 1 <= int(cleaned) <= len(unique_label_values_list):
                        parsed_indices.append(int(cleaned))
                    else:
                        print(f"Index '{cleaned}' is invalid or out of range.")
                        is_valid = False
                        break

                if is_valid and parsed_indices:
                    selected_set: set[int] = set(parsed_indices)
                    if len(selected_set) == len(unique_label_values_list):
                        print("Cannot map ALL classes to 0. At least one must remain for Class 1.")
                        continue

                    zero_class_list: list[Any] = [
                        unique_label_values_list[idx - 1] for idx in selected_set
                    ]
                    one_class_list: list[Any] = [
                        val for val in unique_label_values_list if val not in zero_class_list
                    ]

                    print("\n" + "-" * 60)
                    print("[CONFIRMED BINARY CLASS MAPPING]")
                    print(f"  Target Column: '{chosen_label_col}'")
                    print(f"  Values mapped to 0 (Class 0): {zero_class_list}")
                    print(f"  Values mapped to 1 (Class 1): {one_class_list}")
                    print("-" * 60)

                    remediation_config["binary_class_conversion"] = {
                        "enabled": True,
                        "target_column_name": chosen_label_col,
                        "zero_class_values_list": zero_class_list,
                        "one_class_values_list": one_class_list,
                    }
                    break

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
        except Exception as error_exception:
            print(f"Invalid path or directory permission error: {error_exception}")

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

                def convert_cell_value_to_binary(cell_value: Any) -> Any:
                    # Preserve existing missing / NaN values without artificial imputation
                    if pd.isna(cell_value):
                        return cell_value
                    # Map designated baseline values to integer 0
                    if cell_value in zero_class_values_set:
                        return 0
                    # Map designated remaining values to integer 1
                    if cell_value in one_class_values_set:
                        return 1
                    # Fallback assignment for any unmapped non-null value
                    return 1

                transformed_dataframe[target_column_name] = transformed_dataframe[
                    target_column_name
                ].map(convert_cell_value_to_binary)

                # Count final binary distribution for console audit confirmation
                count_of_zero_values: int = int(
                    (transformed_dataframe[target_column_name] == 0).sum()
                )
                count_of_one_values: int = int(
                    (transformed_dataframe[target_column_name] == 1).sum()
                )
                print(
                    f"[REMEDIATION] Converted column '{target_column_name}' to binary classes "
                    f"(Class 0: {count_of_zero_values:,} rows, Class 1: {count_of_one_values:,} rows)."
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

    except Exception as error_exception:
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

    except Exception as error_exception:
        sys.stderr.write(
            f"[FATAL ERROR] Failed to export processed dataset to: {target_file_path}\n"
            f"Traceback:\n{traceback.format_exc()}\n"
        )
        raise error_exception


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
