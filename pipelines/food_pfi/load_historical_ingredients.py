import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

import psycopg2
from src.config import DB_PARAMS

def load_ingredientes():
    ingredientes = [
        ("agua", "GENERICA", "MockSupplier", 9999),
        ("aceite_coco", "GENERICA", "MockSupplier", 9999),
        ("aceite_girasol", "GENERICA", "MockSupplier", 9999),
        ("aislado_soja_supro_ex32", "SUPRO", "ADM", 9999),
        ("ajo_en_polvo", "GENERICA", "MockSupplier", 9999),
        ("alfa_colorante", "GENERICA", "MockSupplier", 9999),
        ("almidon_acetal700", "ACETAL", "AcetalCorp", 9999),
        ("almidon_firm_tex", "FIRM-TEX", "TexCorp", 9999),
        ("almidon_papa", "GENERICA", "MockSupplier", 9999),
        ("almidon_trigo", "GENERICA", "MockSupplier", 9999),
        ("cc_soja_txt_soyplus", "SOYPLUS", "MockSupplier", 9999),
        ("cc_soja_adm", "ADM", "ADM", 9999),
        ("cc_soja_alpha_adm", "ALPHA", "ADM", 9999),
        ("cc_soja_alpha_dk", "ALPHA", "DKSoy", 9999),
        ("cacao_polvo", "GENERICA", "MockSupplier", 9999),
        ("carragenina_generica", "GENERICA", "MockSupplier", 9999),
        ("carrag_cordis", "CORDIS", "CordisCorp", 9999),
        ("carrag_elbahiense", "ELBAHIENSE", "LocalCarrag", 9999),
        ("carrag_gel_tex_21ex", "GELTEX", "GelCorp", 9999),
        ("carrag_tecno", "TECNO", "TecnoCarrag", 9999),
        ("carrag_tecnoalimenti", "TECNOALIMENTI", "TecnoFood", 9999),
        ("cebolla_polvo", "GENERICA", "MockSupplier", 9999),
        ("colorante_colormix", "COLORMIX", "ColorCorp", 9999),
        ("colorante_rojo7", "ROJO7", "ColorCorp", 9999),
        ("comino", "GENERICA", "MockSupplier", 9999),
        ("dextrosa", "GENERICA", "MockSupplier", 9999),
        ("emulsion_metocel", "METOCEL", "MockSupplier", 9999),
        ("fibra_citrica_cf1", "CF1", "FiberCo", 9999),
        ("fibra_citrica_hf", "HF", "FiberCo", 9999),
        ("fibra_papa", "GENERICA", "MockSupplier", 9999),
        ("fibra_trigo", "GENERICA", "MockSupplier", 9999),
        ("fibra_papa_granotec", "GRANOTEC", "Granotec", 9999),
        ("fecula_mandioca", "GENERICA", "MockSupplier", 9999),
        ("fecula_papa", "GENERICA", "MockSupplier", 9999),
        ("gluten_de_trigo", "GENERICA", "MockSupplier", 9999),
        ("goma_xantica", "GENERICA", "MockSupplier", 9999),
        ("goma_garrofin", "GENERICA", "MockSupplier", 9999),
        ("harina_soja_txt_america_pampa", "AMERICA PAMPA", "SoyCorp", 9999),
        ("harina_soja_txt_rosentek", "ROSENTEK", "Rosentek", 9999),
        ("harina_arroz", "GENERICA", "MockSupplier", 9999),
        ("metilcelulosa", "GENERICA", "MockSupplier", 9999),
        ("metilcelulosa_ts100", "TS100", "CeluloCorp", 9999),
        ("pimenton_ahumado", "GENERICA", "MockSupplier", 9999),
        ("pimenton_dulce", "GENERICA", "MockSupplier", 9999),
        ("pimienta_blanca", "GENERICA", "MockSupplier", 9999),
        ("pimienta_negra", "GENERICA", "MockSupplier", 9999),
        ("provenzal", "GENERICA", "MockSupplier", 9999),
        ("remolacha_polvo", "GENERICA", "MockSupplier", 9999),
        ("sabor_humo_lecker", "LECKER", "LeckerCorp", 9999),
        ("sabor_salchicha_fryma", "FRYMA", "FrymaCo", 9999),
        ("sabor_salchicha_givaudan", "GIVAUDAN", "Givaudan", 9999),
        ("sabor_salchicha_iff", "IFF", "IFF", 9999),
        ("sabor_salchicha_novaron", "NOVARON", "NovaronCo", 9999),
        ("sabor_salchicha_saporiti", "SAPORITI", "Saporiti", 9999),
        ("sabor_salchicha_lecker", "LECKER", "LeckerCorp", 9999),
        ("sal", "GENERICA", "MockSupplier", 9999),
        ("simplistica", "GENERICA", "MockSupplier", 9999),
        ("simplistica_robocoop", "ROBOCOOP", "MockSupplier", 9999),
        ("simplistica_cutter", "CUTTER", "MockSupplier", 9999),
        ("zanahoria_polvo", "GENERICA", "MockSupplier", 9999),
        ("agar_agar", "GENERICA", "MockSupplier", 9999),
        ("colorante", "GENERICA", "MockSupplier", 9999),
        ("sabor", "GENERICA", "MockSupplier", 9999),
    ]

    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()

        cursor.execute("TRUNCATE TABLE dim_ingredientes RESTART IDENTITY CASCADE;")

        query = """
            INSERT INTO dim_ingredientes (nombre, marca, proveedor, costo_unitario_ars)
            VALUES (%s, %s, %s, %s)
        """
        cursor.executemany(query, ingredientes)

        conn.commit()
        print(f"✅ {len(ingredientes)} ingredientes cargados correctamente.")

    except Exception as e:
        print(f"❌ Error cargando ingredientes: {e}")

    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    load_ingredientes()