"""
A* Pathfinding pour OPTIPICK
Trouve le plus court chemin en évitant les obstacles
"""

import heapq


def manhattan_distance(pos1, pos2):
    """
    Distance Manhattan entre deux positions (heuristique pour A*)
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def get_neighbors(pos, grid):
    """
    Retourne les voisins traversables d'une position
    Mouvements : haut, bas, gauche, droite (pas de diagonale)
    
    Args:
        pos: [x, y] position actuelle (coordonnées 1-based)
        grid: grille de navigation (indices 0-based)
    
    Returns:
        Liste de positions [x, y] voisines traversables
    """
    x, y = pos
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    
    # 4 directions possibles (pas de diagonale)
    directions = [
        (0, 1),   # Haut
        (0, -1),  # Bas
        (-1, 0),  # Gauche
        (1, 0)    # Droite
    ]
    
    neighbors = []
    for dx, dy in directions:
        new_x = x + dx
        new_y = y + dy
        
        # Vérifier que la nouvelle position est dans les limites
        if 1 <= new_x <= width and 1 <= new_y <= height:
            # Convertir en indices 0-based pour accéder à la grille
            grid_x = new_x - 1
            grid_y = height - new_y
            
            # Vérifier que la case est traversable
            if grid[grid_y][grid_x] == 1:
                neighbors.append([new_x, new_y])
    
    return neighbors


def astar_path(start, end, grid):
    """
    Algorithme A* pour trouver le plus court chemin
    
    Args:
        start: [x, y] position de départ (coordonnées 1-based)
        end: [x, y] position d'arrivée (coordonnées 1-based)
        grid: grille de navigation [[0/1, ...], ...]
    
    Returns:
        Liste de positions [[x, y], ...] du chemin (incluant start et end)
        Retourne None si aucun chemin n'existe
    """
    # Si start == end, retourner un chemin d'une seule case
    if start == end:
        return [start]
    
    # Vérifier que start et end sont traversables
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    
    start_grid_x = start[0] - 1
    start_grid_y = height - start[1]
    end_grid_x = end[0] - 1
    end_grid_y = height - end[1]
    
    if not (0 <= start_grid_x < width and 0 <= start_grid_y < height):
        print(f"⚠️  Start position {start} hors limites")
        return None
    
    if not (0 <= end_grid_x < width and 0 <= end_grid_y < height):
        print(f"⚠️  End position {end} hors limites")
        return None
    
    if grid[start_grid_y][start_grid_x] == 0:
        print(f"⚠️  Start position {start} est bloquée")
        return None
    
    if grid[end_grid_y][end_grid_x] == 0:
        print(f"⚠️  End position {end} est bloquée")
        return None
    
    # Initialisation A*
    # Priority queue : (f_score, counter, position)
    counter = 0  # Pour départager les positions avec même f_score
    open_set = []
    heapq.heappush(open_set, (0, counter, tuple(start)))
    
    # Dictionnaires pour A*
    came_from = {}  # came_from[pos] = position précédente
    g_score = {tuple(start): 0}  # g_score[pos] = coût depuis start
    f_score = {tuple(start): manhattan_distance(start, end)}  # f_score[pos] = g + h
    
    # Ensemble des positions déjà évaluées
    closed_set = set()
    
    while open_set:
        # Prendre la position avec le plus petit f_score
        current_f, _, current = heapq.heappop(open_set)
        current = list(current)  # Convertir tuple en list
        
        # Si on a atteint la destination
        if current == end:
            # Reconstruire le chemin
            path = [end]
            while tuple(path[-1]) in came_from:
                path.append(came_from[tuple(path[-1])])
            path.reverse()
            return path
        
        closed_set.add(tuple(current))
        
        # Explorer les voisins
        for neighbor in get_neighbors(current, grid):
            neighbor_tuple = tuple(neighbor)
            
            if neighbor_tuple in closed_set:
                continue
            
            # Coût pour atteindre le voisin depuis start
            tentative_g = g_score[tuple(current)] + 1  # Coût = 1 par case
            
            # Si on a trouvé un meilleur chemin vers le voisin
            if neighbor_tuple not in g_score or tentative_g < g_score[neighbor_tuple]:
                came_from[neighbor_tuple] = current
                g_score[neighbor_tuple] = tentative_g
                f = tentative_g + manhattan_distance(neighbor, end)
                f_score[neighbor_tuple] = f
                
                # Ajouter à open_set si pas déjà présent
                counter += 1
                heapq.heappush(open_set, (f, counter, neighbor_tuple))
    
    # Aucun chemin trouvé
    print(f"⚠️  Aucun chemin trouvé de {start} à {end}")
    return None


def calculate_distance(start, end, grid):
    """
    Calcule la distance (nombre de cases) entre deux positions
    
    Args:
        start: [x, y] position de départ
        end: [x, y] position d'arrivée
        grid: grille de navigation
    
    Returns:
        int: nombre de cases du chemin (ou distance Manhattan si pas de chemin)
    """
    path = astar_path(start, end, grid)
    
    if path is None:
        # Fallback sur Manhattan si pas de chemin
        return manhattan_distance(start, end)
    
    # Distance = nombre de cases - 1 (on ne compte pas la case de départ)
    return len(path) - 1


# === TESTS ===
if __name__ == "__main__":
    # Grille de test simple 5x5
    test_grid = [
        [1, 1, 1, 1, 1],  # y=5
        [1, 0, 0, 0, 1],  # y=4
        [1, 0, 1, 0, 1],  # y=3
        [1, 0, 1, 0, 1],  # y=2
        [1, 1, 1, 1, 1]   # y=1
    ]
    
    print("=== TEST A* PATHFINDING ===")
    print("\nGrille de test (1=traversable, 0=bloqué):")
    for y_idx, row in enumerate(test_grid):
        y = 5 - y_idx
        print(f"y={y}: {row}")
    
    # Test 1 : Chemin simple
    print("\n--- Test 1 : Chemin sans obstacle ---")
    start = [1, 1]
    end = [5, 1]
    path = astar_path(start, end, test_grid)
    print(f"De {start} à {end}")
    print(f"Chemin trouvé : {path}")
    print(f"Distance : {len(path)-1} cases")
    
    # Test 2 : Chemin avec obstacle
    print("\n--- Test 2 : Chemin avec contournement ---")
    start = [1, 5]
    end = [5, 5]
    path = astar_path(start, end, test_grid)
    print(f"De {start} à {end}")
    print(f"Chemin trouvé : {path}")
    print(f"Distance : {len(path)-1} cases")
    
    # Test 3 : Pas de chemin possible
    print("\n--- Test 3 : Destination bloquée ---")
    start = [1, 1]
    end = [3, 3]  # Case bloquée
    path = astar_path(start, end, test_grid)
    print(f"De {start} à {end}")
    print(f"Chemin : {path}")
