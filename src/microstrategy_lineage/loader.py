import pandas as pd
import zipfile
import io
import os

def load_platform_analytics(file_path):
    path_str = str(file_path)
    
    def read_file(file_obj):
        # 1. Intento directo y simple (Ideal para los tests de GitHub y CSVs sanos)
        try:
            if hasattr(file_obj, 'seek'): file_obj.seek(0)
            df = pd.read_csv(file_obj, dtype=str)
            if len(df.columns) > 1:
                return df
        except Exception:
            pass
            
        # 2. Intento robusto (Solo si falla el primero, ideal para reportes pesados reales)
        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252', 'utf-16']
        separators = [',', '\t', ';', '|']
        
        for enc in encodings:
            for sep in separators:
                try:
                    if hasattr(file_obj, 'seek'): file_obj.seek(0)
                    df = pd.read_csv(file_obj, encoding=enc, sep=sep, dtype=str, on_bad_lines='skip')
                    if len(df.columns) > 2:
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
    if path_str.endswith('.zip'):
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

    # ---------------------------------------------------------
    # LIMPIEZA
    # ---------------------------------------------------------
    def clean_col(c):
        return str(c).replace('\ufeff', '').strip().replace('"', '')

    current_cols = [clean_col(c) for c in df.columns]
    
    # Alinear cabeceras si la tabla viene movida (Como el Modelo BBVA)
    if 'Object Name' not in current_cols:
        for i in range(min(10, len(df))):
            row_vals = [clean_col(val) for val in df.iloc[i].values]
            if 'Object Name' in row_vals:
                df.columns = row_vals
                df = df.iloc[i+1:].reset_index(drop=True)
                break
        else:
            df.columns = current_cols
    else:
        df.columns = current_cols

    # Eliminar columnas vacías y rellenar nulos
    df = df.loc[:, ~df.columns.isna()]
    df = df.loc[:, [c for c in df.columns if str(c).strip().lower() not in ('', 'nan')]]
    df = df.fillna("")

    return df.to_dict(orient="records")
