import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

def extract_colors_from_soc(file_path):
    colors = {}
    # Namespace definieren
    namespaces = {'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'}

    tree = ET.parse(file_path)
    root = tree.getroot()

    # Iteriere über alle `draw:color`-Elemente
    for color in root.findall('.//draw:color', namespaces):
        color_name = color.get('{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}name')  # Vollständiger Namespace
        color_value = color.get('{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}color')  # Vollständiger Namespace
        if color_name and color_value:
            colors[color_name] = color_value

    return colors

def plot_colors(colors):
    fig, ax = plt.subplots(figsize=(8, len(colors) * 0.5))
    for i, (name, hex_value) in enumerate(colors.items()):
        if len (hex_value) == 7:
            ax.barh(i, 1, color=hex_value, edgecolor='black')
            label = f"{name}: {hex_value}"
            ax.text(0.5, i, label, va='center', ha='center', fontsize=10, color='white' if hex_value != '#ffffff' else 'black')
    ax.set_yticks(range(len(colors)))
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.set_xlim(0, 1)
    ax.set_title("Farben aus TUM_Colors.soc", fontsize=14)
    plt.tight_layout()
    plt.show()

# Beispiel: Farben extrahieren
#colors = extract_colors_from_soc('TUM_Colors.soc')

col = {'TUM:Emphasize:Green': '#a2ad00',
 'TUM:Emphasize:Ivory': '#dad7cb',
 'TUM:Emphasize:LightBlue': '#64a0c8',
 'TUM:Emphasize:LighterBlue': '#98c6ea',
 'TUM:Emphasize:Orange': '#e37222',
 'TUM:Extended:Forest': '#007c30',
 'TUM:Extended:Forest:20%': '#cce5d6',
 'TUM:Extended:Forest:50%': '#80bd98',
 'TUM:Extended:Forest:80%': '#339659',
 'TUM:Extended:Goldenrod': '#f9ba00',
 'TUM:Extended:Goldenrod:20%': '#fef1cc',
 'TUM:Extended:Goldenrod:50%': '#fcdd80',
 'TUM:Extended:Goldenrod:80%': '#fac833',
 'TUM:Extended:Lime': '#679a1d',
 'TUM:Extended:Lime:20%': '#e1ebd2',
 'TUM:Extended:Lime:50%': '#b3cd8e',
 'TUM:Extended:Lime:80%': '#85ae4a',
 'TUM:Extended:Maroon': '#9c0d16',
 'TUM:Extended:Maroon:20%': '#ebcfd0',
 'TUM:Extended:Maroon:50%': '#ce868b',
 'TUM:Extended:Maroon:80%': '#b03d45',
 'TUM:Extended:Navy': '#0f1a5f',
 'TUM:Extended:Navy!20%': '#cfd1df',
 'TUM:Extended:Navy!50%': '#878caf',
 'TUM:Extended:Navy!80%': '#3f497f',
 'TUM:Extended:Pumpkin': '#d64c13',
 'TUM:Extended:Pumpkin:20%': '#f7dbd0',
 'TUM:Extended:Pumpkin:50%': '#eaa689',
 'TUM:Extended:Pumpkin:80%': '#de7042',
 'TUM:Extended:Red': '#c4071b',
 'TUM:Extended:Red:20%': '#f3cdd1',
 'TUM:Extended:Red:50%': '#e2838d',
 'TUM:Extended:Red:80%': '#d03949',
 'TUM:Extended:Teal': '#00778a',
 'TUM:Extended:Teal!50%': '#80bbc5',
 'TUM:Extended:Teal:20%': '#cce4e8',
 'TUM:Extended:Teal:80%': '#3392a1',
 'TUM:Extended:Violet': '#69085a',
 'TUM:Extended:Violet:20%': '#e1cede',
 'TUM:Extended:Violet:50%': '#b484ad',
 'TUM:Extended:Violet:80%': '#87397b',
 'TUM:Extended:Yellow': '#ffdc00',
 'TUM:Extended:Yellow:20%': '#fff8cc',
 'TUM:Extended:Yellow:50%': '#ffee80',
 'TUM:Extended:Yellow:80%': '#ffe333',
 'TUM:Primary:Black': '#000000',
 'TUM:Primary:Blue': '#0073cf',
 'TUM:Primary:White': '#ffffff',
 'TUM:Secondary:DarkBlue': '#005293',
 'TUM:Secondary:DarkBlue:20%': '#ccdce9',
 'TUM:Secondary:DarkBlue:50%': '#80a9c9',
 'TUM:Secondary:DarkBlue:80%': '#3375a9',
 'TUM:Secondary:DarkerBlue': '#003359',
 'TUM:Secondary:DarkerBlue:20%': '#ccd6de',
 'TUM:Secondary:DarkerBlue:50%': '#8099ac',
 'TUM:Secondary:DarkerBlue:80%': '#335c7a',
 'TUM:Secondary:Gray:20%': '#ccccc6',
 'TUM:Secondary:Gray:50%': '#808080',
 'TUM:Secondary:Gray:80%': '#333333'}

color = {
    'TUM:Extended:Maroon': '#9c0d16',
    'TUM:Extended:Red': '#c4071b',
    'TUM:Extended:Red:80%': '#d03949',
    'TUM:Extended:Red:50%': '#e2838d',
    'TUM:Extended:Red:20%': '#f3cdd1',
    'TUM:Extended:Violet:20%': '#e1cede',
    'TUM:Emphasize:LighterBlue': '#98c6ea',
    'TUM:Emphasize:LightBlue': '#64a0c8',
    'TUM:Primary:Blue': '#0073cf',
    'TUM:Secondary:DarkBlue:80%': '#3375a9',
    'TUM:Secondary:DarkerBlue:80%': '#335c7a',
}
plot_colors(col)
