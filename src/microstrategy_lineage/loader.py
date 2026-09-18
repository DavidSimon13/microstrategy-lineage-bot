import pandas as pd
import zipfile
import io
import os

def load_platform_analytics(file_path):
    path_str = str(file_path)
    df = None
    
    # 'utf-8-sig' es la clave mágica que elimina el carácter invisible BOM (\ufeff)
    encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'latin1', 'cp1252']
    separators = [',', '\t', ';']
    
    def try_read(file_obj):
        for enc in encodings:
            for sep in separators:
                try:
                    if hasattr(file_obj, 'seek'):
                        file_obj.seek(0)
                    
                    temp_df = pd.read_csv(file_obj, encoding=enc, sep=sep, on_bad_lines='skip')
                    if len(temp_df.columns) > 3: 
                        return temp_df
                except Exception:
                    continue
        return None

    # Si la ruta apunta a una carpeta (porque se extrajo el ZIP), buscar el CSV adentro
    if os.path.isdir(path_str):
        csv_files = [f for f in os.listdir(path_str) if f.lower().endswith('.csv')]
        if csv_files:
            path_str = os.path.join(path_str, csv_files[0])

    # Manejo de ZIP o archivo directo
    if path_str.endswith('.zip'):
        with zipfile.ZipFile(path_str, 'r') as z:
            csv_files = [name for name in z.namelist() if name.lower().endswith('.csv') and '__MACOSX' not in name]
            
            if not csv_files:
                raise ValueError(f"No se encontró ningún archivo .csv válido dentro del ZIP: {path_str}")
                
            csv_filename = csv_files[0]
            
            with z.open(csv_filename) as f:
                content = f.read()
                df = try_read(io.BytesIO(content))
    else:
        df = try_read(path_str)

    if df is None:
        raise ValueError(f"No se pudo procesar el archivo {path_str}. Verifica su formato.")

    # ---------------------------------------------------------
    # LIMPIEZA EXTREMA DE COLUMNAS (BOM, Comillas, Espacios)
    # ---------------------------------------------------------
    def clean_col(c):
        return str(c).replace('\ufeff', '').strip().replace('"', '')

    current_cols = [clean_col(c) for c in df.columns]
    
    # Detectar cabeceras movidas (Caso BBVA)
    if 'Object Name' not in current_cols:
        for i in range(min(10, len(df))):
            row_vals = [clean_col(val) for val in df.iloc[i].values]
            if 'Object Name' in row_vals:
                df.columns = df.iloc[i]
                df = df.iloc[i+1:].reset_index(drop=True)
                break

    # Asignar nombres limpios definitivos
    df.columns = [clean_col(c) for c in df.columns]

    # Eliminar columnas basura
    df = df.loc[:, ~df.columns.isna()]
    df = df.loc[:, [c for c in df.columns if str(c).strip().lower() not in ('', 'nan')]]

    return df.to_dict(orient="records")
