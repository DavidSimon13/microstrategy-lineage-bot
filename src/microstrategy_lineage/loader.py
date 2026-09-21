import io
import os
import re
import zipfile
from pathlib import Path

import pandas as pd


def _clean_text(value):
    if value is None:
        return ""
    return str(value).replace("\ufeff", "").replace("\x00", "").replace("\u200b", "").strip()


def _normalize_column_name(column_name):
    normalized = _clean_text(column_name).lower()
    normalized = normalized.replace("-", " ").replace("/", " ").replace(".", " ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip().replace(" ", "_")

    aliases = {
        "object_name": "object_name",
        "object_guid": "object_guid",
        "object_location": "object_location",
        "object_type": "object_type",
        "object_type_desc": "object_type",
        "component_object_name": "component_name",
        "component_name": "component_name",
        "component_object_guid": "component_guid",
        "component_guid": "component_guid",
        "component_object_type": "component_type",
        "component_type": "component_type",
        "component_object_type_desc": "component_type",
        "component_type_desc": "component_type",
    }
    return aliases.get(normalized, normalized)


def _resolve_input_path(file_path):
    if file_path is None:
        return ""
    path = Path(str(file_path))
    if path.exists():
        return str(path)
    repo_candidate = Path(__file__).resolve().parents[2] / path
    return str(repo_candidate if repo_candidate.exists() else path)


def _read_tabular(file_obj, suffix=""):
    """Lee CSV o Excel y devuelve un DataFrame con la cabecera correcta."""
    if suffix.lower() in {".xlsx", ".xls", ".xlsm"}:
        try:
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            sheets = pd.read_excel(file_obj, sheet_name=None, dtype=str)
            frames = [frame for frame in sheets.values() if frame is not None and not frame.empty]
            return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    encodings = ["utf-16", "utf-8-sig", "utf-8", "cp1252", "latin1"]
    for encoding in encodings:
        for separator in [",", "\t", ";", "|"]:
            try:
                if hasattr(file_obj, "seek"):
                    file_obj.seek(0)
                frame = pd.read_csv(
                    file_obj,
                    encoding=encoding,
                    sep=separator,
                    dtype=str,
                    on_bad_lines="skip",
                )
                if len(frame.columns) > 1:
                    return frame
            except Exception:
                continue
    return pd.DataFrame()


def _normalize_frame(df):
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    df.columns = [_normalize_column_name(column) for column in df.columns]

    required = {"object_name", "object_guid", "object_location", "object_type"}
    if not required.issubset(set(df.columns)):
        for index in range(min(10, len(df))):
            values = [_clean_text(value) for value in df.iloc[index].tolist()]
            if any("object name" in value.lower() for value in values):
                df.columns = [_normalize_column_name(value) for value in values]
                df = df.iloc[index + 1:].reset_index(drop=True)
                break

    df = df.loc[:, [column for column in df.columns if _clean_text(column).lower() not in {"", "nan"}]]
    df = df.fillna("")

    text_columns = {
        "object_name", "object_guid", "object_location", "object_type",
        "component_name", "component_guid", "component_type",
    }
    for column in text_columns.intersection(df.columns):
        df[column] = df[column].astype(str).map(_clean_text)

    return df


def load_platform_analytics(file_path):
    path_str = _resolve_input_path(file_path)

    if os.path.isdir(path_str):
        files = [name for name in os.listdir(path_str) if Path(name).suffix.lower() in {".csv", ".xlsx", ".xls", ".xlsm"}]
        if not files:
            return []
        path_str = os.path.join(path_str, files[0])

    suffix = Path(path_str).suffix.lower()
    if suffix == ".zip":
        with zipfile.ZipFile(path_str, "r") as archive:
            names = [name for name in archive.namelist() if Path(name).suffix.lower() in {".csv", ".xlsx", ".xls", ".xlsm"} and "__MACOSX" not in name]
            if not names:
                return []
            name = names[0]
            with archive.open(name) as file_obj:
                df = _read_tabular(io.BytesIO(file_obj.read()), Path(name).suffix)
    else:
        df = _read_tabular(path_str, suffix)

    df = _normalize_frame(df)
    return df.to_dict(orient="records") if not df.empty else []
