"""Load and validate user-supplied tabular data without persisting uploads."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable

import pandas as pd


class IngestError(ValueError):
    """A file or column-mapping problem that can be shown to a user."""


@dataclass(frozen=True)
class LoadResult:
    """A loaded table and the non-fatal notices produced while reading it."""

    frame: pd.DataFrame
    source_name: str
    sheet_name: str | None
    rows_omitted: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class MappingResult:
    """The normalized internal table and a summary of cleaning decisions."""

    frame: pd.DataFrame
    empty_comments_removed: int
    duplicate_respondents_removed: int


def _source_name(source: str | Path | BinaryIO, filename: str | None) -> str:
    if filename:
        return filename
    if isinstance(source, (str, Path)):
        return Path(source).name
    candidate = getattr(source, "name", None)
    if candidate:
        return Path(str(candidate)).name
    raise IngestError("The uploaded file needs a .csv or .xlsx filename.")


def _rewind(source: str | Path | BinaryIO) -> None:
    if hasattr(source, "seek"):
        source.seek(0)


def _read_csv(
    source: str | Path | BinaryIO, *, row_cap: int
) -> tuple[pd.DataFrame, str]:
    """Read common CSV encodings while keeping the original stream reusable."""

    encodings = ("utf-8-sig", "utf-8", "cp1252")
    last_error: UnicodeDecodeError | None = None
    for encoding in encodings:
        _rewind(source)
        try:
            return (
                pd.read_csv(source, nrows=row_cap + 1, encoding=encoding),
                encoding,
            )
        except UnicodeDecodeError as exc:
            last_error = exc

    raise IngestError(
        "The CSV encoding could not be detected. Save it as UTF-8 and try again."
    ) from last_error


def list_excel_sheets(
    source: str | Path | BinaryIO, filename: str | None = None
) -> list[str]:
    """Return workbook sheet names without loading comment data."""

    name = _source_name(source, filename)
    if Path(name).suffix.lower() != ".xlsx":
        raise IngestError("Sheet selection is available only for XLSX files.")
    _rewind(source)
    try:
        workbook = pd.ExcelFile(source, engine="openpyxl")
    except Exception as exc:  # pandas/openpyxl errors vary by file corruption
        raise IngestError("The XLSX workbook could not be opened.") from exc
    finally:
        _rewind(source)
    return list(workbook.sheet_names)


def load_table(
    source: str | Path | BinaryIO,
    *,
    filename: str | None = None,
    sheet_name: str | None = None,
    row_cap: int = 5_000,
) -> LoadResult:
    """Load a CSV or XLSX file and enforce the MVP row cap."""

    if row_cap < 1:
        raise ValueError("row_cap must be at least 1")

    name = _source_name(source, filename)
    extension = Path(name).suffix.lower()
    if extension not in {".csv", ".xlsx"}:
        raise IngestError("Please upload a CSV or XLSX file.")

    _rewind(source)
    try:
        if extension == ".csv":
            frame, source_encoding = _read_csv(source, row_cap=row_cap)
            selected_sheet = None
        else:
            source_encoding = None
            selected_sheet = sheet_name or 0
            frame = pd.read_excel(
                source,
                sheet_name=selected_sheet,
                nrows=row_cap + 1,
                engine="openpyxl",
            )
    except ValueError as exc:
        raise IngestError(f"The selected sheet or table could not be read: {exc}") from exc
    except Exception as exc:
        raise IngestError("The file could not be read as a valid table.") from exc
    finally:
        _rewind(source)

    if not len(frame.columns):
        raise IngestError("The file has no columns.")
    if len(frame) == 0:
        raise IngestError("The file has column headers but no data rows.")

    rows_omitted = max(0, len(frame) - row_cap)
    if rows_omitted:
        frame = frame.iloc[:row_cap].copy()

    warnings: list[str] = []
    if rows_omitted:
        warnings.append(
            f"The MVP analyzes the first {row_cap:,} rows; additional rows were omitted."
        )
    if source_encoding == "cp1252":
        warnings.append(
            "This CSV used Windows-1252 encoding. Exporting as UTF-8 is recommended."
        )
    unnamed = [str(column) for column in frame.columns if str(column).startswith("Unnamed:")]
    if unnamed:
        warnings.append(
            "One or more columns have blank headers and should not be selected for mapping."
        )

    normalized_sheet = None if extension == ".csv" else str(selected_sheet)
    return LoadResult(
        frame=frame,
        source_name=name,
        sheet_name=normalized_sheet,
        rows_omitted=rows_omitted,
        warnings=tuple(warnings),
    )


def map_columns(
    frame: pd.DataFrame,
    *,
    comment_column: str,
    date_or_hearing_column: str | None = None,
    respondent_id_column: str | None = None,
    subgroup_columns: Iterable[str] = (),
) -> MappingResult:
    """Map user headers to the internal schema and clean required comment text."""

    if comment_column not in frame.columns:
        raise IngestError("Select a valid column containing the comment text.")

    optional = [
        column
        for column in (date_or_hearing_column, respondent_id_column)
        if column is not None
    ]
    requested = [comment_column, *optional, *subgroup_columns]
    missing = [column for column in requested if column not in frame.columns]
    if missing:
        raise IngestError("Mapped columns are missing: " + ", ".join(map(str, missing)))

    if len(set(requested)) != len(requested):
        raise IngestError("Each source column can be mapped only once.")

    mapped = frame.loc[:, requested].copy()
    rename_map: dict[str, str] = {comment_column: "comment_text"}
    if date_or_hearing_column:
        rename_map[date_or_hearing_column] = "date_or_hearing"
    if respondent_id_column:
        rename_map[respondent_id_column] = "respondent_id"
    rename_map.update({column: f"subgroup__{column}" for column in subgroup_columns})
    mapped = mapped.rename(columns=rename_map)

    comments = mapped["comment_text"].fillna("").astype(str).str.strip()
    keep_comments = comments.ne("")
    empty_removed = int((~keep_comments).sum())
    mapped = mapped.loc[keep_comments].copy()
    mapped["comment_text"] = comments.loc[keep_comments]

    duplicates_removed = 0
    if "respondent_id" in mapped.columns:
        ids = mapped["respondent_id"].fillna("").astype(str).str.strip()
        repeated = ids.ne("") & ids.duplicated(keep="first")
        duplicates_removed = int(repeated.sum())
        mapped = mapped.loc[~repeated].copy()

    if mapped.empty:
        raise IngestError("No usable comments remain after empty rows are removed.")

    return MappingResult(
        frame=mapped.reset_index(drop=True),
        empty_comments_removed=empty_removed,
        duplicate_respondents_removed=duplicates_removed,
    )
