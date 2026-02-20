"""
Module de visualisation 2D de l'entrepôt OPTIPICK
Génère une carte avec matplotlib basée sur l'image fournie
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


# Couleurs basées sur la légende de l'image
COLORS = {
    'passage': '#FFB6C1',      # Rose (zone de passage)
    'storage': '#ADD8E6',      # Bleu clair (stockage produit)
    'preparation': '#90EE90',  # Vert clair (préparation commandes)
    'refrigerated': '#DDA0DD', # Violet/lilas (zone réfrigérée)
    'entry': '#87CEEB',        # Bleu (entrée/sortie)
    'pickup': '#FFD700',       # Jaune (zone de pick-up)
    'robot_zone': '#F5DEB3',   # Beige (ZONE ROBOT ONLY)
    'grid': '#CCCCCC',         # Gris pour la grille
    'default': '#FFB6C1',      # Rose par défaut (cases blanches)
    'prep_access': '#FFA500',  # Orange (cases d'accès préparation)
    'entry_gray': '#808080',   # Gris (case entry point)
}


def create_warehouse_map(warehouse, show_grid=True):
    """
    Crée la carte 2D de l'entrepôt
    
    Args:
        warehouse: données de warehouse.json
        show_grid: afficher la grille (True/False)
    
    Returns:
        fig, ax: objets matplotlib
    """
    width = warehouse['dimensions']['width']
    height = warehouse['dimensions']['height']
    
    # Créer la figure
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect('equal')
    
    # Titre
    ax.set_title("🏭 Plan de l'Entrepôt OPTIPICK", fontsize=16, fontweight='bold', pad=20)
    
    # Labels des axes
    ax.set_xlabel("X (colonnes)", fontsize=12)
    ax.set_ylabel("Y (lignes)", fontsize=12)
    
    # Grille si demandée
    if show_grid:
        ax.set_xticks(np.arange(0, width+1, 1))
        ax.set_yticks(np.arange(0, height+1, 1))
        ax.grid(True, color=COLORS['grid'], linewidth=0.5, alpha=0.5)
    
    # === FOND ROSE POUR TOUTES LES CASES ===
    # Dessiner un fond rose par défaut pour toutes les cases
    for x in range(1, width + 1):
        for y in range(1, height + 1):
            rect = patches.Rectangle(
                (x - 1, y - 1),
                1, 1,
                linewidth=0.5,
                edgecolor='black',
                facecolor=COLORS['default'],
                alpha=0.7
            )
            ax.add_patch(rect)
    
    # === DESSINER LES ZONES PAR-DESSUS ===
    zones = warehouse.get('zones', {})
    
    # Ordre de dessin (du fond vers le haut)
    zone_order = ['passage', 'storage', 'pickup', 'refrigerated', 'preparation', 'entry_exit']
    zone_color_map = {
        'passage': COLORS['passage'],
        'storage': COLORS['storage'],
        'pickup': COLORS['pickup'],
        'refrigerated': COLORS['refrigerated'],
        'preparation': COLORS['preparation'],
        'entry_exit': COLORS['entry']
    }
    
    for zone_type in zone_order:
        if zone_type in zones:
            color = zone_color_map.get(zone_type, '#FFFFFF')
            coords = zones[zone_type]['coords']
            
            for coord in coords:
                x, y = coord
                # Convertir coordonnées: [x, y] → rectangle à (x-1, y-1)
                rect = patches.Rectangle(
                    (x - 1, y - 1),
                    1, 1,
                    linewidth=0.5,
                    edgecolor='black',
                    facecolor=color,
                    alpha=0.7
                )
                ax.add_patch(rect)
    
    # === ZONE ROBOT ONLY - ENCADRÉ EN POINTILLÉS ===
    # Zone robot complète : X de 0 à 3 inclus, Y de 0 à 6 inclus
    # (en coordonnées matplotlib 0-based)
    robot_zone_x_start = 0  # Colonnes 1-4 (warehouse)
    robot_zone_y_start = 0  # Lignes 1-7 (warehouse)
    robot_zone_width = 4    # 4 colonnes (0,1,2,3)
    robot_zone_height = 7   # 7 lignes (0,1,2,3,4,5,6)
    
    # Dessiner le rectangle en pointillés
    robot_rect = patches.Rectangle(
        (robot_zone_x_start, robot_zone_y_start),
        robot_zone_width,
        robot_zone_height,
        linewidth=2.5,
        linestyle='--',  # Pointillés
        edgecolor='#8B4513',  # Marron foncé
        facecolor='none',  # Pas de remplissage (transparent)
        alpha=0.8,
        zorder=5
    )
    ax.add_patch(robot_rect)
    
    # Ajouter le texte au centre de la zone
    robot_zone_center_x = robot_zone_x_start + robot_zone_width / 2
    robot_zone_center_y = robot_zone_y_start + robot_zone_height / 2
    
    ax.text(
        robot_zone_center_x, robot_zone_center_y,
        'ZONE\nROBOT\nONLY',
        fontsize=12,
        fontweight='bold',
        ha='center',
        va='center',
        color='#8B4513',  # Marron foncé
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.7, edgecolor='none')
    )
    
    # === CASES SPÉCIALES ===
    
    # 1. Cases autour de la zone de préparation [6,5] en ORANGE
    prep_access_coords = [
        [5, 4], [6, 4], [7, 4],  # En bas
        [5, 5], [7, 5],           # Gauche et droite
        [5, 6], [6, 6], [7, 6]    # En haut
    ]
    
    for coord in prep_access_coords:
        x, y = coord
        rect = patches.Rectangle(
            (x - 1, y - 1),
            1, 1,
            linewidth=0.5,
            edgecolor='black',
            facecolor=COLORS['prep_access'],
            alpha=0.7
        )
        ax.add_patch(rect)
    
    # 2. Case entry point [6,10] en GRIS
    entry_coord = [6, 10]
    rect = patches.Rectangle(
        (entry_coord[0] - 1, entry_coord[1] - 1),
        1, 1,
        linewidth=0.5,
        edgecolor='black',
        facecolor=COLORS['entry_gray'],
        alpha=0.7
    )
    ax.add_patch(rect)
    
    # 3. Case à droite de l'entry [7,10] en ROSE
    right_entry_coord = [7, 10]
    rect = patches.Rectangle(
        (right_entry_coord[0] - 1, right_entry_coord[1] - 1),
        1, 1,
        linewidth=0.5,
        edgecolor='black',
        facecolor=COLORS['default'],
        alpha=0.7
    )
    ax.add_patch(rect)
    
    # === ENTRY POINT ===
    entry = warehouse.get('entry_point', [6, 10])
    ax.plot(
        entry[0] - 0.5, entry[1] - 0.5,
        marker='o',
        markersize=12,
        color='blue',
        markeredgecolor='black',
        markeredgewidth=2,
        label='Entry Point'
    )
    
    # === PRÉPARATION ZONE ===
    prep = warehouse.get('preparation_zone', [6, 5])
    ax.plot(
        prep[0] - 0.5, prep[1] - 0.5,
        marker='s',
        markersize=12,
        color='green',
        markeredgecolor='black',
        markeredgewidth=2,
        label='Préparation'
    )
    
    return fig, ax


def add_agent_trajectory(ax, trajectory, agent_id, agent_type, color='red', alpha=0.6, depot_positions=None):
    """
    Ajoute la trajectoire d'un agent sur la carte
    AVEC marqueurs de dépôt ◆
    
    Args:
        ax: axes matplotlib
        trajectory: dict {minute: [x, y]}
        agent_id: ID de l'agent
        agent_type: type d'agent (robot, human, cart)
        color: couleur de la trajectoire
        alpha: transparence
        depot_positions: liste des positions de dépôt [[x,y], ...] pour cet agent
    """
    if not trajectory:
        return
    
    # Extraire les positions dans l'ordre chronologique
    times = sorted(trajectory.keys())
    positions = [trajectory[t] for t in times]
    
    if not positions:
        return
    
    # Convertir en coordonnées matplotlib (centrer sur les cases)
    x_coords = [p[0] - 0.5 for p in positions]
    y_coords = [p[1] - 0.5 for p in positions]
    
    # Tracer la trajectoire
    ax.plot(
        x_coords, y_coords,
        color=color,
        linewidth=2.5,
        alpha=alpha,
        label=f'{agent_id} ({agent_type})',
        marker='.',
        markersize=2
    )
    
    # Marquer le départ (cercle ●)
    ax.plot(
        x_coords[0], y_coords[0],
        marker='o',
        markersize=10,
        color=color,
        markeredgecolor='black',
        markeredgewidth=1.5,
        zorder=10
    )
    
    # Marquer l'arrivée (étoile ★) - toujours à l'entry point maintenant
    ax.plot(
        x_coords[-1], y_coords[-1],
        marker='*',
        markersize=14,
        color=color,
        markeredgecolor='black',
        markeredgewidth=1.5,
        zorder=10
    )
    
    # Marquer les dépôts (losange ◆)
    if depot_positions:
        for depot_pos in depot_positions:
            ax.plot(
                depot_pos[0] - 0.5, depot_pos[1] - 0.5,
                marker='D',  # Losange/diamant
                markersize=10,
                color=color,
                markeredgecolor='black',
                markeredgewidth=1.5,
                zorder=10,
                alpha=0.9
            )


def create_legend_patch(color, label):
    """Crée un patch pour la légende"""
    return patches.Patch(facecolor=color, edgecolor='black', label=label, alpha=0.7)


def add_warehouse_legend(ax):
    """Ajoute la légende des zones de l'entrepôt"""
    legend_elements = [
        create_legend_patch(COLORS['entry_gray'], 'Point de départ / arrivé'),
        create_legend_patch(COLORS['preparation'], 'Préparation commandes'),
        create_legend_patch(COLORS['prep_access'], 'Dépôt des articles'),
        create_legend_patch(COLORS['refrigerated'], 'Zone réfrigérée'),
        create_legend_patch(COLORS['pickup'], 'Zone de pick-up'),
        create_legend_patch(COLORS['storage'], 'Stockage produit'),
        create_legend_patch(COLORS['default'], 'Zone de passage (rose)'),
        create_legend_patch(COLORS['robot_zone'], 'ZONE ROBOT ONLY'),
    ]
    
    ax.legend(
        handles=legend_elements,
        loc='upper left',
        bbox_to_anchor=(1.02, 1),
        fontsize=10,
        frameon=True,
        fancybox=True,
        shadow=True
    )


# === TEST ===
if __name__ == "__main__":
    import json
    
    # Charger warehouse
    with open('warehouse.json', 'r') as f:
        warehouse = json.load(f)
    
    # Créer la carte
    fig, ax = create_warehouse_map(warehouse, show_grid=True)
    add_warehouse_legend(ax)
    
    plt.tight_layout()
    plt.savefig('warehouse_map_test.png', dpi=150, bbox_inches='tight')
    print("✓ Carte générée : warehouse_map_test.png")
    plt.show()