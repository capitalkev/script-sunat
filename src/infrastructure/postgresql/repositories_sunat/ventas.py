# src/infrastructure/postgresql/repositories_sunat/ventas.py

import json

from sqlalchemy import text
from sqlalchemy.orm import Session
import pandas as pd


class VentasRepository:
    def __init__(self, db: Session):
        self.db = db
        self.engine = db.get_bind()

    def existe_periodo(self, ruc: str, periodo: str) -> bool:
        """Verifica si ya existen ventas para este cliente y periodo en la BD."""
        query = text(
            """
            SELECT 1 FROM ventas_sunat 
            WHERE ruc = :ruc AND periodo = :per 
            LIMIT 1
        """
        )
        resultado = self.db.execute(query, {"ruc": ruc, "per": periodo}).fetchone()
        return resultado is not None

    def guardar_lote_ventas(self, df_limpio: pd.DataFrame, ruc: str, periodo: str) -> int:
        if df_limpio.empty:
            return 0

        tabla_temp = f"temp_ventas_{ruc}_{periodo}"

        # Usar self.engine.begin() asegura un COMMIT si todo sale bien, o un ROLLBACK si falla
        with self.engine.begin() as conn:
            # 1. Subimos la data temporal
            df_limpio.to_sql(
                name=tabla_temp, con=conn, if_exists='replace', index=False, chunksize=1000
            )
            
            # 2. UPSERT a la tabla real
            query_upsert = text(f"""
                INSERT INTO ventas_sunat (
                    ruc, razon_social, periodo, fecha_emision, fecha_vcto_pago, 
                    tipo_cp_doc, serie_cdp, nro_cp_doc, nro_doc_identidad, 
                    cliente_razon_social, total_cp, moneda, tipo_cambio, 
                    serie_cp_modificado, nro_cp_modificado,
                    ruc_cliente, periodo_tributario
                )
                SELECT 
                    ruc, razon_social, periodo, fecha_emision, fecha_vcto_pago, 
                    tipo_cp_doc, serie_cdp, nro_cp_doc, nro_doc_identidad, 
                    cliente_razon_social, total_cp, moneda, tipo_cambio, 
                    serie_cp_modificado, nro_cp_modificado,
                    :ruc_cliente, :periodo
                FROM {tabla_temp}
                ON CONFLICT (ruc_cliente, tipo_cp_doc, serie_cdp, nro_cp_doc) 
                DO NOTHING;
            """)
            
            conn.execute(query_upsert, {"ruc_cliente": ruc, "periodo": periodo})
            conn.execute(text(f"DROP TABLE {tabla_temp};"))
            
        return len(df_limpio)
    
    def guardar_errores(self, registros_malos: list[dict], ruc: str, periodo: str, motivo: str) -> None:
        """Guarda los registros que no pasaron las reglas de negocio en la tabla de errores."""
        if not registros_malos:
            return

        query_errores = text("""
            INSERT INTO ventas_sunat_errores (ruc_cliente, periodo_tributario, motivo_error, datos_crudos)
            VALUES (:ruc, :per, :motivo, :datos)
        """)

        try:
            for registro in registros_malos:
                self.db.execute(query_errores, {
                    "ruc": ruc,
                    "per": periodo,
                    "motivo": motivo,
                    "datos": json.dumps(registro)  # Se convierte a JSON aquí, en la infraestructura
                })
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
