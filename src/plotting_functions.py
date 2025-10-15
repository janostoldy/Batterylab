import re
import io

colors = {
        'TUM:Extended:Violet': '#69085a',  # Violett
        'TUM:Primary:Blue': '#0073cf',  # Blau
        'TUM:Extended:Teal': '#00778a',  # Türkis / Cyan
        'TUM:Extended:Forest': '#007c30',  # Grün
        'TUM:Extended:Lime': '#679a1d',  # Gelbgrün
        'TUM:Extended:yellow80': '#ffe333',  # Gelb
        'TUM:Extended:Goldenrod': '#f9ba00',  # Dunkelgelb
        'TUM:Extended:Pumpkin': '#d64c13',  # Rötliches Orange
        'TUM:Extended:Maroon': '#9c0d16',  # Dunkelrot, noch unter Rot
        'TUM:Extended:Red': '#c4071b'  # Rot
    }
colors_short = {
        'TUM:Extended:Violet': '#69085a',  # Violett
        'TUM:Primary:Blue': '#0073cf',  # Blau
        'TUM:Extended:Forest': '#007c30',  # Grün
        'TUM:Extended:yellow80': '#ffe333',  # Gelbgrün
         'TUM:Extended:Pumpkin': '#d64c13',  # Rötliches Orange
        'TUM:Extended:Red': '#c4071b'  # Rot
    }

def extract_sort_keys(name):
    # Suche nach den relevanten Zahlen
    cycle_match = re.search(r'Cycle_(\d+)', name)
    qcell_match = re.search(r'Qcell_(\d+)', name)
    ima_match = re.search(r'ImA_(\d+)', name)

    # Wandle zu int um, wenn gefunden – sonst fallback auf eine große Zahl
    cycle = int(cycle_match.group(1)) if cycle_match else float('inf')
    qcell = int(qcell_match.group(1)) if qcell_match else float('inf')
    ima = int(ima_match.group(1)) if ima_match else float('inf')

    return (cycle, qcell, ima)

def get_linestyles():
    color_list = list(colors.values())
    line_styles = ['solid', 'dash', 'dot', 'dashdot']
    dot_styles = ['circle', 'square', 'diamond', 'cross']
    combination_line = []
    combimation_dot = []
    for style in line_styles:
        for name, hex_value in colors.items():
            combination_line.append({
                'color': hex_value,
                'line_style': style
            })
    for marker in dot_styles:
        for name, hex_value in colors.items():
            combimation_dot.append({
                'color': hex_value,
                'marker_type': marker
            })
    return combination_line, combimation_dot

# Nicht mehr verwendet
def download_button(col, fig, key):
    fig.update_layout(
        template="plotly",  # <- wichtig!
        paper_bgcolor='white',
        plot_bgcolor='white',
        font_color='black',
        legend_title_font_color='black',
        xaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',  # Farbe des Grids
            gridwidth=1  # Dicke der Linien
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            gridwidth=1
        )
    )

    # --- Export als SVG ---
    # Temporären Buffer für SVG-Datei anlegen
    #try:
    svg_buffer = io.BytesIO()
    fig.write_image(svg_buffer, format='svg', engine='kaleido', width=1200, height=800)
    svg_data = svg_buffer.getvalue()
    dis = False
    #except Exception as e:
        #svg_data = b""
        #dis = True
    col.download_button(
        label="Download als SVG",
        data=svg_data,
        file_name="plot.svg",
        mime="image/svg+xml",
        key=key,
        use_container_width=True,
        disabled=dis,
    )