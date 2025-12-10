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
        
    # === RENOMBRAR COLUMNAS DE STATS: stat_hp -> hp, etc. ===
    rename_map = {
        'stat_hp': 'HP',
        'stat_attack': 'Attack',
        'stat_defense': 'Defense',
        'stat_special-attack': 'Special Attack',
        'stat_special-defense': 'Special Defense',
        'stat_speed': 'Speed'
    }
    df = df.rename(columns=rename_map)
    
    # Columnas de estadísticas base YA renombradas
    stats_cols = ['HP', 'Attack', 'Defense', 'Special Attack', 'Special Defense', 'Speed']
    
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
# Definimos las columnas numéricas que queremos analizar (YA SIN prefijo stat_)
cols_to_analyze = ['HP', 'Attack', 'Defense', 'Special Attack', 'Special Defense', 'Speed']

# Creamos una tabla pivotante (agrupada) con los datos filtrados
heatmap_data = df_filtered.groupby('primary_type')[cols_to_analyze].mean()

# 2. Crear el gráfico
fig_heatmap = px.imshow(
    heatmap_data,
    text_auto=".0f",                 # Muestra el número entero dentro de la celda
    aspect="auto",                   # Ajusta el ancho automáticamente
    color_continuous_scale="RdBu",
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
    index=1,  # Por defecto seleccionamos la justa
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
# Columnas que queremos analizar (SIN stat_)
stat_cols = ['HP', 'Attack', 'Defense', 'Special Attack', 'Special Defense', 'Speed']

# Calculamos la media agrupada por Categoría
mean_legendary_stats = df_legendary[stat_cols].mean()
mean_mythical_stats = df_mythical[stat_cols].mean()
mean_normal_stats = df_normal[stat_cols].mean()

normal_label = df_normal['Category'].iloc[0] if not df_normal.empty else 'Normal'

stats_df = pd.DataFrame({
    'Category': ['Legendario'] * len(stat_cols) + ['Mítico'] * len(stat_cols) + [normal_label] * len(stat_cols),
    'Statistic': stat_cols * 3,
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
    'Category': ['Legendario', 'Mítico', normal_label],
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

# --- 4. MEJOR POKEMON POR TIPO Y STAT ---


st.subheader("Mejor Pokémon por tipo y estadística")
st.markdown(
    "Para cada estadística base, se muestra el Pokémon con mejor valor "
    "en cada tipo y también los mejores entre Legendarios y Míticos. "
    "Los legendarios y míticos **no** cuentan para el mejor de su tipo."
)

# Columnas de stats que vamos a usar
best_stat_cols = [
    'HP',
    'Attack',
    'Defense',
    'Special Attack',
    'Special Defense',
    'Speed',
    'Total Stats'  # 👈 opción de suma de todas las stats
]

# 1️⃣ Selector de estadística
selected_stat_key = st.selectbox(
    "Selecciona la estadística a analizar:",
    options=best_stat_cols
)

# Determinar la columna real del DataFrame
stat_column = selected_stat_key if selected_stat_key != "Total Stats" else "total_stats"

# 2️⃣ Checkbox para usar tipo secundario o primario
use_secondary = st.checkbox(
    "Usar tipo secundario en lugar del tipo primario",
    value=False
)

type_col = "secondary_type" if use_secondary else "primary_type"

# 3️⃣ Checkbox para usar el mínimo en vez del máximo
use_min = st.checkbox(
    "Mostrar el peor Pokémon por estadística",
    value=False
)

# Lista de tipos presentes (sin "-" ni NaN)
type_groups = (df_filtered[type_col].dropna().unique().tolist())
type_groups = [g for g in type_groups if g != "-"]

# Añadir grupos especiales si existen
all_groups = type_groups.copy()
if not df_filtered[df_filtered['is_legendary'] == True].empty:
    all_groups.append('Legendario')
if not df_filtered[df_filtered['is_mythical'] == True].empty:
    all_groups.append('Mítico')

records = []

# 4️⃣ Calcular mejor/peor Pokémon por grupo
for g in all_groups:
    if g == 'Legendario':
        subset = df_filtered[df_filtered['is_legendary'] == True]
    elif g == 'Mítico':
        subset = df_filtered[df_filtered['is_mythical'] == True]
    else:
        subset = df_filtered[
            (df_filtered[type_col] == g) &
            (df_filtered['is_legendary'] == False) &
            (df_filtered['is_mythical'] == False)
        ]

    if subset.empty or stat_column not in subset.columns:
        continue

    # Elegir índice según máximo o mínimo
    if use_min:
        idx = subset[stat_column].idxmin()
    else:
        idx = subset[stat_column].idxmax()

    best_row = subset.loc[idx]

    records.append({
        "Group": g,
        "BestValue": best_row[stat_column],
        "Pokemon": best_row['name']
    })

# DataFrame con resultados
best_by_type_df = pd.DataFrame(records)

if not best_by_type_df.empty:
    # 5️⃣ Orden dinámico: mayor → menor (o menor → mayor)
    plot_df = best_by_type_df.sort_values("BestValue", ascending=use_min == True)

    # 6️⃣ Colores fijos por tipo
    color_map = {
        "normal": "#A8A77A",
        "fire": "#EE8130",
        "water": "#6390F0",
        "electric": "#F7D02C",
        "grass": "#7AC74C",
        "ice": "#96D9D6",
        "fighting": "#C22E28",
        "poison": "#A33EA1",
        "ground": "#E2BF65",
        "flying": "#A98FF3",
        "psychic": "#F95587",
        "bug": "#A6B91A",
        "rock": "#B6A136",
        "ghost": "#735797",
        "dragon": "#6F35FC",
        "dark": "#705746",
        "steel": "#B7B7CE",
        "fairy": "#D685AD",
        "Legendario": "#777777",
        "Mítico": "#FF6FD8"
    }

    # 7️⃣ Crear gráfica
    modo_texto = "menor" if use_min else "mayor"
    fig_best = px.bar(
        plot_df,
        x="BestValue",
        y="Group",
        orientation="h",
        text="Pokemon",
        title=f"{'Peor' if use_min else 'Mejor'} Pokémon por grupo para {selected_stat_key}"
    )

    fig_best.update_traces(
        marker_color=[color_map[g] for g in plot_df["Group"]],
        textposition="outside"
    )

    # Orden del eje Y según el ranking
    fig_best.update_yaxes(
        categoryorder="array",
        categoryarray=plot_df["Group"].tolist()[::-1]  # invertido por gráfica horizontal
    )

    # Layout
    fig_best.update_layout(
        showlegend=False,
        xaxis_title=f"Valor de la estadística ({modo_texto})",
        yaxis_title="Tipo / Grupo",
        height=600
    )

    st.plotly_chart(fig_best, use_container_width=True)
else:
    st.info("No hay datos suficientes para mostrar el ranking con los filtros actuales.")



# --- 5. DETALLE DE POKÉMON (Utilidad y Evitar Errores) ---

st.header("Detalle Individual de Pokémon")
st.markdown("Esta sección permite ver los datos de un Pokémon individual (usado para probar la carga de datos).")

pokemon_name = st.selectbox("Busca un Pokémon para ver sus datos:", df_filtered['name'].sort_values())

# El valor máximo para la normalización (255 es el máx. teórico de una stat base)
MAX_STAT = 255 

if pokemon_name:
    row = df[df['name'] == pokemon_name].iloc[0]
    
    # Categoría: Legendario / Mítico / Normal
    if bool(row['is_legendary']):
        category_label = "Legendario"
    elif bool(row['is_mythical']):
        category_label = "Mítico"
    else:
        category_label = "Normal"

    col_img, col_data = st.columns([1, 3])
    
    with col_img:
        # Muestra el sprite/imagen del Pokémon
        if pd.notna(row['sprite_url']):
            st.image(row['sprite_url'], width=150)
            
    with col_data:
        st.write(f"**Tipo Primario:** {row['primary_type']}")
        st.write(f"**Tipo Secundario:** {row['secondary_type']}")
        st.write(f"**Generación:** {row['generation']}")
        st.write(f"**Categoría:** {category_label}")  # 👈 NUEVA LÍNEA
        
        st.markdown("##### Estadísticas Base:")
        
        def display_stat_progress(stat_name_key):
            stat_value = row[stat_name_key]
            # Normaliza el valor a un porcentaje (de 0 a 100)
            normalized_value = int((stat_value / MAX_STAT) * 100)
            st.progress(normalized_value, text=f"**{stat_name_key}:** {stat_value}")

        display_stat_progress('HP')
        display_stat_progress('Attack')
        display_stat_progress('Defense')
        display_stat_progress('Special Attack')
        display_stat_progress('Special Defense')
        display_stat_progress('Speed')

