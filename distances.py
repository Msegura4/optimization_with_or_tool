from astar import calculate_distance as astar_distance, manhattan_distance


def calculate_distance_matrix(products, entry_point, navigation_grid=None):
    """
    Calcule la matrice des distances entre :
    - entry_point (point de départ/arrivée)
    - tous les pickup_locations des produits
    
    Si navigation_grid est fournie, utilise A* pour éviter les obstacles.
    Sinon, utilise la distance Manhattan simple.
    
    Args:
        products: liste des produits avec pickup_location
        entry_point: [x, y] point d'entrée
        navigation_grid: grille [[0/1,...]] optionnelle (0=bloqué, 1=traversable)
    
    Returns:
        dict {
            'entry': entry_point,
            'locations': {product_id: pickup_location},
            'distances': {(from, to): distance},
            'grid': navigation_grid ou None
        }
    """
    # Préparer les locations
    locations = {'entry': entry_point}
    
    for product in products:
        locations[product['id']] = product['pickup_location']
    
    # Calculer toutes les distances
    distances = {}
    all_points = list(locations.keys())
    
    use_astar = navigation_grid is not None
    
    if use_astar:
        print(f"  🗺️  Utilisation de A* avec navigation_grid (évite obstacles)")
    else:
        print(f"  ⚠️  Pas de navigation_grid → utilisation Manhattan simple")
    
    for i, from_key in enumerate(all_points):
        for to_key in all_points:
            from_pos = locations[from_key]
            to_pos = locations[to_key]
            
            if use_astar:
                # Utiliser A* avec obstacles
                dist = astar_distance(from_pos, to_pos, navigation_grid)
            else:
                # Fallback sur Manhattan
                dist = manhattan_distance(from_pos, to_pos)
            
            distances[(from_key, to_key)] = dist
    
    return {
        'entry': entry_point,
        'locations': locations,
        'distances': distances,
        'grid': navigation_grid
    }

if __name__ == "__main__":
    from loader import load_warehouse, load_products
    
    # Charger les données
    warehouse = load_warehouse('warehouse.json')
    products = load_products('products.json')
    
    entry_point = warehouse['entry_point']
    navigation_grid = warehouse.get('navigation_grid', None)
    
    # Calculer la matrice
    distance_data = calculate_distance_matrix(products, entry_point, navigation_grid)
    
    print("=== MATRICE DES DISTANCES ===")
    print(f"Point d'entrée : {distance_data['entry']}")
    print(f"Nombre de locations : {len(distance_data['locations'])}")
    print(f"Nombre de distances calculées : {len(distance_data['distances'])}")
    print(f"Grille navigation : {'✓ Activée' if distance_data['grid'] else '❌ Désactivée'}")
    
    # Exemples de distances
    print("\n=== EXEMPLES DE DISTANCES ===")
    print(f"Entry → Product_001 pickup : {distance_data['distances'][('entry', 'Product_001')]} cases")
    print(f"Product_001 → Product_002 : {distance_data['distances'][('Product_001', 'Product_002')]} cases")
    print(f"Product_001 → Product_089 (food) : {distance_data['distances'][('Product_001', 'Product_089')]} cases")
    print(f"Entry → Product_089 pickup : {distance_data['distances'][('entry', 'Product_089')]} cases")
