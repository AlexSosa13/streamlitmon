import streamlit as st
import pandas as pd
import plotly.express as px

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
st.markdown("Analizando las fortalezas y debilidades según el tipo de Pokémon.")

# 1. Preparar los datos: Agrupar por Tipo Primario y sacar el promedio
# Definimos las columnas numéricas que queremos analizar
cols_to_analyze = ['stat_hp', 'stat_attack', 'stat_defense', 'stat_special-attack', 'stat_special-defense', 'stat_speed']

# Creamos una tabla pivotante (agrupada) con los datos filtrados
heatmap_data = df_filtered.groupby('primary_type')[cols_to_analyze].mean()

# 2. Crear el gráfico
fig_heatmap = px.imshow(
    heatmap_data,
    text_auto=".0f",                 # Muestra el número entero dentro de la celda
    aspect="auto",                   # Ajusta el ancho automáticamente
    color_continuous_scale="RdBu",# Escala de colores (puedes probar 'Magma' o 'RdBu')
    title="Promedio de Estadísticas Base por Tipo"
)

# Mejora visual: Mover las etiquetas del eje X arriba para facilitar la lectura
fig_heatmap.update_xaxes(side="top")
fig_heatmap.update_layout(yaxis_title="Tipo Primario")

# 3. Mostrar el gráfico en Streamlit
st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("---")

st.markdown("Comparando la brecha de poder entre Pokémon especiales y normales")

# 1. INTERACTIVIDAD: Selector de modo de comparación
comparison_mode = st.radio(
    "¿Qué grupo de 'Normales' quieres comparar?",
    ["Todos los Normales", 
     "Completamente Evolucionados"],
    index=1, # Por defecto seleccionamos la justa
    horizontal=True
)

# 2. LÓGICA DE FILTRADO
# Crear copias para no afectar el dataframe global
df_legendary = df_filtered[df_filtered['is_legendary'] == True].copy()
df_mythical = df_filtered[df_filtered['is_mythical'] == True].copy()
df_normal = df_filtered[(df_filtered['is_legendary'] == False) & (df_filtered['is_mythical'] == 0)].copy()

# Etiquetar categorías
df_legendary['Category'] = 'Legendario'
df_mythical['Category'] = 'Mítico'

if "Completamente Evolucionados" in comparison_mode:
    df_normal = df_normal[df_normal['can_evolve'] == False]
    df_normal['Category'] = 'Normal (Max. Potencial)'
else:
    df_normal['Category'] = 'Normal (Todos)'

# Unimos todo en un dataframe temporal para calcular medias
df_comparison = pd.concat([df_legendary, df_mythical, df_normal])

# 3. PREPARACIÓN DE DATOS PARA GRÁFICO (PANDAS AVANZADO)
# Columnas que queremos analizar
stat_cols = ['stat_hp', 'stat_attack', 'stat_defense', 'stat_special-attack', 'stat_special-defense', 'stat_speed']

# Calculamos la media agrupada por Categoría
mean_legendary_stats = df_legendary[stat_cols].mean()
mean_mythical_stats = df_mythical[stat_cols].mean()
mean_normal_stats = df_normal[stat_cols].mean()

stats_df = pd.DataFrame({
    'Category': ['Legendario'] * len(stat_cols) + ['Mítico'] * len(stat_cols) + ['Normal'] * len(stat_cols),
    'Statistic': list(mean_legendary_stats.index) * 3,
    'Mean_Value': list(mean_legendary_stats.values) + list(mean_mythical_stats.values) + list(mean_normal_stats.values)
})

# 4. GRÁFICO DE BARRAS AGRUPADAS
fig_comp = px.bar(
    stats_df,
    x='Mean_Value',
    y='Statistic',
    color='Category',
    barmode='group',
    orientation='h',
    title=f"Comparativa de Stats Medios ({comparison_mode})",
)

fig_comp.update_layout(xaxis_title="Valor Promedio", yaxis_title="Estadística")
st.plotly_chart(fig_comp, use_container_width=True)

# 5. GRÁFICO DE TOTALES (SUMA DE PROMEDIOS)
total_mean_legendary_stats = mean_legendary_stats.sum()
total_mean_mythical_stats = mean_mythical_stats.sum()
total_mean_normal_stats = mean_normal_stats.sum()

total_stats_sum_df = pd.DataFrame({
    'Category': ['Legendario', 'Mítico', 'Normal'],
    'Total_Mean_Stats': [total_mean_legendary_stats, total_mean_mythical_stats, total_mean_normal_stats]
})

fig_total = px.bar(
    total_stats_sum_df,
    x='Total_Mean_Stats',
    y='Category',
    color='Category',
    orientation='h',
    title="Poder Total Promedio (Suma de todas las stats)",
)
st.plotly_chart(fig_total, use_container_width=True)

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