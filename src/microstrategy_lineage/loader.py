import pandas as pd
import zipfile
import io
import os

def load_platform_analytics(file_path):
    path_str = str(file_path)
    df = None

    def try_read(file_obj):
        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'utf-16']
        separators = [',', ';', '\t']
        
        # 1. Intentar lectura perfecta (sin saltar líneas, protege archivos originales)
        for enc in encodings:
            for sep in separators:
                try:
                    if hasattr(file_obj, 'seek'): file_obj.seek(0)
                    temp_df = pd.read_csv(file_obj, encoding=enc, sep=sep, dtype=str)
                    if len(temp_df.columns) > 3 and any('Object' in str(c) for c in temp_df.columns):
                        return temp_df
                except Exception:
                    continue
                    
        # 2. Si falla, intentar lectura flexible (saltando líneas corruptas para los nuevos)
        for enc in encodings:
            for sep in separators:
                try:
                    if hasattr(file_obj, 'seek'): file_obj.seek(0)
                    temp_df = pd.read_csv(file_obj, encoding=enc, sep=sep, on_bad_lines='skip', dtype=str)
                    if len(temp_df.columns) > 3:
                        cols_str = " ".join([str(c).lower() for c in temp_df.columns])
                        top_rows_str = " ".join([str(v).lower() for v in temp_df.head(5).values.flatten()])
                        if 'object' in cols_str or 'object' in top_rows_str or 'guid' in cols_str:
                            return temp_df
                except Exception:
                    continue
        return None

    # Detectar si es carpeta (ZIP extraído)
    if os.path.isdir(path_str):
        csv_files = [f for f in os.listdir(path_str) if f.lower().endswith('.csv')]
        if csv_files:
            path_str = os.path.join(path_str, csv_files[0])
        else:
            raise ValueError(f"No se encontró ningún .csv en la carpeta: {path_str}")

    # Detectar si es archivo ZIP
    if path_str.endswith('.zip'):
        with zipfile.ZipFile(path_str, 'r') as z:
            csv_files = [name for name in z.namelist() if name.lower().endswith('.csv') and '__MACOSX' not in name]
            if not csv_files:
                raise ValueError(f"No se encontró un .csv válido en el ZIP: {path_str}")
            with z.open(csv_files[0]) as f:
                content = f.read()
                df = try_read(io.BytesIO(content))
    else:
        df = try_read(path_str)

    if df is None:
        raise ValueError(f"No se pudo procesar el archivo {path_str}. Verifica su formato.")

    # ---------------------------------------------------------
    # LIMPIEZA DE CABECERAS Y COLUMNAS
    # ---------------------------------------------------------
    def clean_col(c):
        return str(c).replace('\ufeff', '').strip().replace('"', '')

    current_cols = [clean_col(c) for c in df.columns]
    
    # Subir cabeceras movidas si la fila 1 es basura (Caso BBVA)
    if 'Object Name' not in current_cols:
        for i in range(min(10, len(df))):
            row_vals = [clean_col(val) for val in df.iloc[i].values]
            if 'Object Name' in row_vals:
                df.columns = df.iloc[i]
                df = df.iloc[i+1:].reset_index(drop=True)
                break

    # Asignar nombres limpios a las columnas
    df.columns = [clean_col(c) for c in df.columns]

    # Eliminar columnas sin nombre y convertir todo a strings limpios
    df = df.loc[:, ~df.columns.isna()]
    df = df.loc[:, [c for c in df.columns if str(c).strip().lower() not in ('', 'nan')]]
    df = df.fillna("")

    return df.to_dict(orient="records")
