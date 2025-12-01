import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="StreamlitMon",
    page_icon="🐾",
    layout="wide"
)

# Título y encabezado principal
st.title("Tablero de Análisis de Pokémon - StreamlitMon")
st.markdown("""
Bienvenido al esqueleto del dashboard. Aquí escribiremos el código para cada visualización de datos.
""")

st.markdown("---")

# --- 1. CARGA Y PRE-PROCESAMIENTO DE DATOS ---

@st.cache_data
def load_and_preprocess_data():
    """Carga y realiza la limpieza y cálculos esenciales del DataFrame."""
    try:
        df = pd.read_csv("pokedex_completa_full.csv")
    except FileNotFoundError:
        st.error("Error: No se encontró el archivo 'pokedex_completa_full.csv'. Por favor, comprueba que el archivo se encuentra en la carpeta.")
        st.stop()
        
    # Columnas de estadísticas base
    stats_cols = ['stat_hp', 'stat_attack', 'stat_defense', 'stat_special-attack', 'stat_special-defense', 'stat_speed']
    
    # Cálculo: Total Stats (para medir el poder general)
    df['total_stats'] = df[stats_cols].sum(axis=1)

    # Limpieza: Función para extraer solo el tipo primario (el primero de la lista)
    def get_primary_type(type_str):
        try:
            if isinstance(type_str, str) and "," in type_str:
                return type_str.split(",")[0]
            return type_str
        except:
            return "unknown"
    
    def get_secondary_type(type_str):
        try:
            if isinstance(type_str, str) and "," in type_str:
                return type_str.split(",")[1]
            return "-"
        except:
            return "unknown"


    df['primary_type'] = df['types'].apply(get_primary_type)
    df['secondary_type'] = df['types'].apply(get_secondary_type)

    
    # Crear una columna combinada para Legendario/Mítico
    df['is_special'] = df['is_legendary'] | df['is_mythical']
    
    return df

df = load_and_preprocess_data()

# --- 2. BARRA LATERAL (SIDEBAR) Y FILTROS ---

st.sidebar.header("Filtros Globales")

# Filtro 1: Generación
generations = sorted(df['generation'].unique())
selected_gens = st.sidebar.multiselect(
    "Selecciona Generaciones",
    options=generations,
    default=generations
)

# Filtro 2: Legendarios/Míticos
show_special = st.sidebar.checkbox("Incluir Legendarios/Míticos", value=True)

# APLICAR FILTROS
df_filtered = df[df['generation'].isin(selected_gens)]

if not show_special:
    df_filtered = df_filtered[df_filtered['is_special'] == 0]

st.sidebar.markdown("---")
st.sidebar.info(f"**Pokémon seleccionados:** {len(df_filtered)}")

# --- 3. SECCIÓN DE VISUALIZACIONES ---

st.header("Visualizaciones")
st.markdown("Aquí añadiremos las visualizaciones para responder preguntas varias.")

st.markdown("---")

# --- 4. DETALLE DE POKÉMON (Utilidad y Evitar Errores) ---

st.header("Detalle Individual de Pokémon")
st.markdown("Esta sección permite ver los datos de un Pokémon individual (usado para probar la carga de datos).")

pokemon_name = st.selectbox("Busca un Pokémon para ver sus datos:", df_filtered['name'].sort_values())

# El valor máximo para la normalización (255 es el máx. teórico de una stat base)
MAX_STAT = 255 

if pokemon_name:
    row = df[df['name'] == pokemon_name].iloc[0]
    
    col_img, col_data = st.columns([1, 3])
    
    with col_img:
        # Muestra el sprite/imagen del Pokémon
        if pd.notna(row['sprite_url']):
            st.image(row['sprite_url'], width=150)
            
    with col_data:
        st.write(f"**Tipo Primario:** {row['primary_type']}")
        st.write(f"**Tipo Secundario:** {row['secondary_type']}")
        st.write(f"**Generación:** {row['generation']}")
        
        st.markdown("##### Estadísticas Base:")
        
        def display_stat_progress(stat_name_key, display_name):
            stat_value = row[stat_name_key]
            # Normaliza el valor a un porcentaje (de 0 a 100)
            normalized_value = int((stat_value / MAX_STAT) * 100)
            st.progress(normalized_value, text=f"**{display_name}:** {stat_value}")
        
        display_stat_progress('stat_hp', 'HP')
        display_stat_progress('stat_attack', 'Attack')
        display_stat_progress('stat_defense', 'Defense')
        display_stat_progress('stat_special-attack', 'Special Attack')
        display_stat_progress('stat_special-defense', 'Special Defense')
        display_stat_progress('stat_speed', 'Speed')