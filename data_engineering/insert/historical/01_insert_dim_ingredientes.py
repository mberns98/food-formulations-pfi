import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3] 
sys.path.append(str(BASE_DIR))

import psycopg2
from src.config import DB_PARAMS

def load_ingredientes():
    ingredientes = [
        ("agua", "GENERICA", "MockSupplier", 9999, 100),
        ("aceite_coco", "GENERICA", "MockSupplier", 9999, 100),
        ("aceite_girasol", "GENERICA", "MockSupplier", 9999, 100),
        ("aislado_soja_supro_ex32", "SUPRO", "ADM", 9999, 100),
        ("ajo_en_polvo", "GENERICA", "MockSupplier", 9999, 100),
        ("alfa_colorante", "GENERICA", "MockSupplier", 9999, 100),
        ("almidon_acetal700", "ACETAL", "AcetalCorp", 9999, 100),
        ("almidon_firm_tex", "FIRM-TEX", "TexCorp", 9999, 100),
        ("almidon_papa", "GENERICA", "MockSupplier", 9999, 100),
        ("almidon_trigo", "GENERICA", "MockSupplier", 9999, 100),
        ("cc_soja_txt_soyplus", "SOYPLUS", "MockSupplier", 9999, 100),
        ("cc_soja_adm", "ADM", "ADM", 9999, 100),
        ("cc_soja_alpha_adm", "ALPHA", "ADM", 9999, 100),
        ("cc_soja_alpha_dk", "ALPHA", "DKSoy", 9999, 100),
        ("cacao_polvo", "GENERICA", "MockSupplier", 9999, 100),
        ("carragenina_generica", "GENERICA", "MockSupplier", 9999, 100),
        ("carrag_cordis", "CORDIS", "CordisCorp", 9999, 100),
        ("carrag_elbahiense", "ELBAHIENSE", "LocalCarrag", 9999, 100),
        ("carrag_gel_tex_21ex", "GELTEX", "GelCorp", 9999, 100),
        ("carrag_tecno", "TECNO", "TecnoCarrag", 9999, 100),
        ("carrag_tecnoalimenti", "TECNOALIMENTI", "TecnoFood", 9999, 100),
        ("cebolla_polvo", "GENERICA", "MockSupplier", 9999, 100),
        ("colorante_colormix", "COLORMIX", "ColorCorp", 9999, 100),
        ("colorante_rojo7", "ROJO7", "ColorCorp", 9999, 100),
        ("comino", "GENERICA", "MockSupplier", 9999, 100),
        ("dextrosa", "GENERICA", "MockSupplier", 9999, 100),
        ("emulsion_metocel", "METOCEL", "MockSupplier", 9999, 100),
        ("fibra_citrica_cf1", "CF1", "FiberCo", 9999, 100),
        ("fibra_citrica_hf", "HF", "FiberCo", 9999, 100),
        ("fibra_papa", "GENERICA", "MockSupplier", 9999, 100),
        ("fibra_trigo", "GENERICA", "MockSupplier", 9999, 100),
        ("fibra_papa_granotec", "GRANOTEC", "Granotec", 9999, 100),
        ("fecula_mandioca", "GENERICA", "MockSupplier", 9999, 100),
        ("fecula_papa", "GENERICA", "MockSupplier", 9999, 100),
        ("gluten_de_trigo", "GENERICA", "MockSupplier", 9999, 100),
        ("goma_xantica", "GENERICA", "MockSupplier", 9999, 100),
        ("goma_garrofin", "GENERICA", "MockSupplier", 9999, 100),
        ("harina_soja_txt_america_pampa", "AMERICA PAMPA", "SoyCorp", 9999, 100),
        ("harina_soja_txt_rosentek", "ROSENTEK", "Rosentek", 9999, 100),
        ("harina_arroz", "GENERICA", "MockSupplier", 9999, 100),
        ("metilcelulosa", "GENERICA", "MockSupplier", 9999, 100),
        ("metilcelulosa_ts100", "TS100", "CeluloCorp", 9999, 100),
        ("pimenton_ahumado", "GENERICA", "MockSupplier", 9999, 100),
        ("pimenton_dulce", "GENERICA", "MockSupplier", 9999, 100),
        ("pimienta_blanca", "GENERICA", "MockSupplier", 9999, 100),
        ("pimienta_negra", "GENERICA", "MockSupplier", 9999, 100),
        ("provenzal", "GENERICA", "MockSupplier", 9999, 100),
        ("remolacha_polvo", "GENERICA", "MockSupplier", 9999, 100),
        ("sabor_humo_lecker", "LECKER", "LeckerCorp", 9999, 100),
        ("sabor_salchicha_fryma", "FRYMA", "FrymaCo", 9999, 100),
        ("sabor_salchicha_givaudan", "GIVAUDAN", "Givaudan", 9999, 100),
        ("sabor_salchicha_iff", "IFF", "IFF", 9999, 100),
        ("sabor_salchicha_novaron", "NOVARON", "NovaronCo", 9999, 100),
        ("sabor_salchicha_saporiti", "SAPORITI", "Saporiti", 9999, 100),
        ("sabor_salchicha_lecker", "LECKER", "LeckerCorp", 9999, 100),
        ("sal", "GENERICA", "MockSupplier", 9999, 100),
        ("simplistica", "GENERICA", "MockSupplier", 9999, 100),
        ("simplistica_robocoop", "ROBOCOOP", "MockSupplier", 9999, 100),
        ("simplistica_cutter", "CUTTER", "MockSupplier", 9999, 100),
        ("zanahoria_polvo", "GENERICA", "MockSupplier", 9999, 100),
        ("agar_agar", "GENERICA", "MockSupplier", 9999, 100),
        ("colorante", "GENERICA", "MockSupplier", 9999, 100),
        ("sabor", "GENERICA", "MockSupplier", 9999, 100),
    ]

    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()

        print("🧹 Limpiando carga histórica previa...")
        cursor.execute("DELETE FROM model.dim_ingredientes WHERE source = 'historical';")
        query = """
            INSERT INTO model.dim_ingredientes (nombre, marca, proveedor, costo_unitario_ars, costo_unitario_usd, source)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        ingredientes_with_source = [(*ing, 'historical') for ing in ingredientes]

        cursor.executemany(query, ingredientes_with_source)

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