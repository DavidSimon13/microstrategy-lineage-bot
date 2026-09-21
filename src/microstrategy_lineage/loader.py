import io
import os
import re
import zipfile
from pathlib import Path

import pandas as pd


def _clean_text(value):
    if value is None:
        return ""
    value = str(value)
    value = value.replace("\ufeff", "")
    value = value.replace("\x00", "")
    value = value.replace("\u200b", "")
    value = value.strip()
    return value


def _normalize_column_name(column_name):
    normalized = _clean_text(column_name)
    normalized = normalized.lower()
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace("/", " ")
    normalized = normalized.replace(".", " ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = normalized.strip()
    normalized = normalized.replace(" ", "_")

    alias_map = {
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

    return alias_map.get(normalized, normalized)


def _resolve_input_path(file_path):
    """Resuelve rutas relativas desde la raíz del repositorio."""
    if file_path is None:
        return ""

    path = Path(str(file_path))

    if path.exists():
        return str(path)

    repo_root = Path(__file__).resolve().parents[2]
    repo_candidate = repo_root / path
    if repo_candidate.exists():
        return str(repo_candidate)

    return str(path)


def load_platform_analytics(file_path):
    path_str = _resolve_input_path(file_path)

    def read_file(file_obj):
        # 1. Intento directo y simple (ideal para CSVs sanos)
        try:
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            df = pd.read_csv(file_obj, dtype=str)
            if len(df.columns) > 1:
                return df
        except Exception:
            pass

        # 2. Intento robusto con encodings y separadores
        encodings = ['utf-16', 'utf-8-sig', 'utf-8', 'latin1', 'cp1252']
        separators = [None, ',', '\t', ';', '|']

        for enc in encodings:
            for sep in separators:
                try:
                    if hasattr(file_obj, 'seek'):
                        file_obj.seek(0)
                    kwargs = {'encoding': enc, 'dtype': str, 'on_bad_lines': 'skip'}
                    if sep is not None:
                        kwargs['sep'] = sep
                    else:
                        kwargs['engine'] = 'python'
                    df = pd.read_csv(file_obj, **kwargs)
                    if len(df.columns) > 1:
                        return df
                except Exception:
                    continue
        return pd.DataFrame()

    df = None

    # Manejo de carpetas
    if os.path.isdir(path_str):
        csv_files = [f for f in os.listdir(path_str) if f.lower().endswith('.csv')]
        if csv_files:
            path_str = os.path.join(path_str, csv_files[0])
        else:
            return []

    # Manejo de ZIPs
    if path_str.lower().endswith('.zip'):
        with zipfile.ZipFile(path_str, 'r') as z:
            csv_files = [name for name in z.namelist() if name.lower().endswith('.csv') and '__MACOSX' not in name]
            if not csv_files:
                return []
            with z.open(csv_files[0]) as f:
                df = read_file(io.BytesIO(f.read()))
    else:
        df = read_file(path_str)

    if df is None or df.empty:
        return []

    # Normalización de columnas para los CSV de MicroStrategy
    df.columns = [_normalize_column_name(col) for col in df.columns]

    # Si el CSV viene con cabecera desplazada, se corrige
    required = {'object_name', 'object_guid', 'object_location', 'object_type'}
    if not required.issubset(set(df.columns)):
        for i in range(min(10, len(df))):
            row_vals = [_clean_text(val) for val in df.iloc[i].values]
            if any('object name' in str(val).lower() for val in row_vals):
                df.columns = [_normalize_column_name(val) for val in row_vals]
                df = df.iloc[i + 1:].reset_index(drop=True)
                break

    # Limpieza final
    df = df.loc[:, ~df.columns.isna()]
    df = df.loc[:, [c for c in df.columns if str(c).strip().lower() not in ('', 'nan')]]
    df = df.fillna("")

    for col in list(df.columns):
        if col in ('object_name', 'object_guid', 'component_name', 'component_guid', 'object_location', 'object_type', 'component_type'):
            df[col] = df[col].astype(str).apply(_clean_text)

    return df.to_dict(orient='records')

