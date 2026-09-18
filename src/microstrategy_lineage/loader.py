import pandas as pd
import zipfile
import io

def load_platform_analytics(file_path):
    path_str = str(file_path)
    df = None
    
    # Lista de codificaciones y separadores comunes en exportaciones de MicroStrategy
    encodings = ['utf-8', 'utf-16', 'latin1', 'cp1252']
    separators = [',', '\t', ';']
    
    def try_read(file_obj):
        for enc in encodings:
            for sep in separators:
                try:
                    # Si es un objeto en memoria (BytesIO), regresar el puntero al inicio
                    if hasattr(file_obj, 'seek'):
                        file_obj.seek(0)
                    
                    # Intentamos leer ignorando líneas corruptas
                    temp_df = pd.read_csv(file_obj, encoding=enc, sep=sep, on_bad_lines='skip')
                    
                    # Si detecta más de 3 columnas, significa que leyó correctamente el formato
                    if len(temp_df.columns) > 3: 
                        return temp_df
                except Exception:
                    continue
        return None

    # Detectar si es un archivo ZIP o un CSV normal
    if path_str.endswith('.zip'):
        with zipfile.ZipFile(path_str, 'r') as z:
            csv_filename = z.namelist()[0]
            with z.open(csv_filename) as f:
                # Cargamos el contenido en memoria para poder reintentar leerlo varias veces
                content = f.read()
                df = try_read(io.BytesIO(content))
    else:
        df = try_read(path_str)

    if df is None:
        raise ValueError(f"No se pudo procesar el archivo {path_str}. Verifica su formato.")

    # ---------------------------------------------------------
    # LIMPIEZA AUTOMÁTICA DE FORMATOS RAROS
    # ---------------------------------------------------------
    
    # 1. Detectar y arreglar cabeceras movidas (Caso "Modelo BBVA")
    # Buscamos 'Object Name' limpio de comillas
    current_cols = [str(c).strip().replace('"', '') for c in df.columns]
    
    if 'Object Name' not in current_cols:
        for i in range(min(10, len(df))):
            row_vals = [str(val).strip().replace('"', '') for val in df.iloc[i].values]
            if 'Object Name' in row_vals:
                df.columns = df.iloc[i]
                df = df.iloc[i+1:].reset_index(drop=True)
                break

    # 2. Limpiar nombres de columnas (quitar comillas, espacios, etc.)
    df.columns = [str(c).strip().replace('"', '') for c in df.columns]

    # 3. Eliminar columnas "basura" o sin nombre
    df = df.loc[:, ~df.columns.isna()]
    df = df.loc[:, [c for c in df.columns if str(c).strip().lower() not in ('', 'nan')]]

    # 4. Devolver los datos listos para Maya
    return df.to_dict(orient="records")
