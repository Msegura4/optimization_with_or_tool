import json
from distances import manhattan_distance
from astar import astar_path


def calculate_agent_trajectory(agent, products_route, entry_point, distance_data, start_delay=0, navigation_grid=None, assigned_depot=None):
    """
    Calcule la trajectoire complète d'un agent minute par minute
    INCLUT les retours au dépôt (case unique) et retour final à l'entry point
    
    Args:
        agent: dict de l'agent
        products_route: liste des produits triés par visit_time
        entry_point: coordonnées [x, y] du point d'entrée
        distance_data: données des distances
        start_delay: délai de départ en minutes (pour éviter collisions)
        navigation_grid: grille de navigation [[0/1,...]] (optionnel)
        assigned_depot: [x, y] case de dépôt assignée à cet agent (unique)
    
    Returns:
        dict {minute: [x, y]} - position de l'agent à chaque minute
        list: positions des dépôts effectués [[x,y], ...]
    """
    trajectory = {}
    depot_positions = []  # Pour marquer les dépôts
    
    # Vitesse de l'agent (m/min)
    speed_m_per_min = agent['speed'] * 60  # m/s -> m/min
    meters_per_cell = 5  # 1 case = 5 mètres
    cells_per_min = speed_m_per_min / meters_per_cell
    
    # Départ à l'entry point avec délai
    current_pos = entry_point.copy()
    current_time = start_delay
    
    # Si pas de dépôt assigné, utiliser [6,5] par défaut (ne devrait pas arriver)
    if assigned_depot is None:
        assigned_depot = [6, 5]
    
    if products_route:
        for i, product_item in enumerate(products_route):
            target_pos = product_item['product_data']['pickup_location']
            visit_time = product_item['visit_time'] + start_delay
            
            # Aller au produit
            path = calculate_path(current_pos, target_pos, navigation_grid)
            
            for step_pos in path:
                trajectory[current_time] = step_pos.copy()
                current_time += 1
                
                if step_pos == target_pos:
                    break
            
            # Rester sur place (picking)
            while current_time <= visit_time:
                trajectory[current_time] = target_pos.copy()
                current_time += 1
            
            current_pos = target_pos.copy()
            
            # === VÉRIFIER SI RETOUR AU DÉPÔT NÉCESSAIRE ===
            is_last_product = (i == len(products_route) - 1)
            
            if not is_last_product:
                current_trip = product_item.get('trip_number', 1)
                next_trip = products_route[i + 1].get('trip_number', 1)
                
                # Si changement de voyage → retour au dépôt (case assignée)
                if next_trip != current_trip:
                    # Tracer le retour au dépôt assigné
                    depot_path = calculate_path(current_pos, assigned_depot, navigation_grid)
                    for step_pos in depot_path:
                        trajectory[current_time] = step_pos.copy()
                        current_time += 1
                    
                    # Rester 2 min au dépôt
                    for _ in range(2):
                        trajectory[current_time] = assigned_depot.copy()
                        current_time += 1
                    
                    # Marquer ce dépôt
                    depot_positions.append(assigned_depot.copy())
                    
                    current_pos = assigned_depot.copy()
            
            # Si c'est le dernier produit → retour au dépôt puis à l'entry point
            elif is_last_product:
                # 1. Retour au dépôt assigné
                depot_path = calculate_path(current_pos, assigned_depot, navigation_grid)
                for step_pos in depot_path:
                    trajectory[current_time] = step_pos.copy()
                    current_time += 1
                
                # Rester 2 min au dépôt (dépôt final)
                for _ in range(2):
                    trajectory[current_time] = assigned_depot.copy()
                    current_time += 1
                
                # Marquer ce dépôt
                depot_positions.append(assigned_depot.copy())
                
                current_pos = assigned_depot.copy()
                
                # 2. Retour à l'entry point
                entry_path = calculate_path(current_pos, entry_point, navigation_grid)
                for step_pos in entry_path:
                    trajectory[current_time] = step_pos.copy()
                    current_time += 1
                
                # Position finale à l'entry point
                trajectory[current_time] = entry_point.copy()
    
    return trajectory, depot_positions


def calculate_path(start, end, navigation_grid=None):
    """
    Calcule le chemin le plus court entre deux positions
    
    Si navigation_grid fournie : utilise A* (évite obstacles)
    Sinon : utilise chemin Manhattan simple (X puis Y)
    
    Args:
        start: [x, y] position de départ
        end: [x, y] position d'arrivée
        navigation_grid: grille [[0/1,...]] optionnelle
    
    Returns:
        list de positions [[x1,y1], [x2,y2], ...]
    """
    if navigation_grid is not None:
        # Utiliser A* avec obstacles
        path = astar_path(start, end, navigation_grid)
        
        if path is None:
            # Fallback sur Manhattan si A* échoue
            print(f"⚠️  A* failed for {start}→{end}, fallback to Manhattan")
            return calculate_path_manhattan(start, end)
        
        return path
    else:
        # Fallback sur Manhattan simple
        return calculate_path_manhattan(start, end)


def calculate_path_manhattan(start, end):
    """
    Chemin Manhattan simple (X puis Y) - ancien comportement
    """
    path = []
    current = start.copy()
    
    # Se déplacer d'abord en X, puis en Y
    while current[0] != end[0]:
        if current[0] < end[0]:
            current[0] += 1
        else:
            current[0] -= 1
        path.append(current.copy())
    
    while current[1] != end[1]:
        if current[1] < end[1]:
            current[1] += 1
        else:
            current[1] -= 1
        path.append(current.copy())
    
    return path


def detect_collisions(agents_trajectories):
    """
    Détecte les collisions entre agents
    
    Args:
        agents_trajectories: dict {agent_id: {minute: [x,y]}}
    
    Returns:
        list de collisions [(agent1_id, agent2_id, minute, position)]
    """
    collisions = []
    agent_ids = list(agents_trajectories.keys())
    
    # Comparer chaque paire d'agents
    for i, agent1_id in enumerate(agent_ids):
        for agent2_id in agent_ids[i+1:]:
            traj1 = agents_trajectories[agent1_id]
            traj2 = agents_trajectories[agent2_id]
            
            # Trouver les minutes communes
            common_times = set(traj1.keys()) & set(traj2.keys())
            
            for t in common_times:
                pos1 = traj1[t]
                pos2 = traj2[t]
                
                # Collision si même position
                if pos1 == pos2:
                    collisions.append((agent1_id, agent2_id, t, pos1))
    
    return collisions

def check_and_adjust_collisions(solution, agents, entry_point, distance_data, max_iterations=250, navigation_grid=None):
    """
    Vérifie les collisions et ajuste si nécessaire
    Assigne une case de dépôt unique à chaque agent
    
    Args:
        solution: résultat de l'optimizer
        agents: liste des agents
        entry_point: point d'entrée
        distance_data: données distances
        max_iterations: nombre max d'itérations pour résoudre collisions
        navigation_grid: grille de navigation [[0/1,...]] (optionnel)
    
    Returns:
        dict avec trajectoires, collisions, et dépôts
    """
    print("\n=== VÉRIFICATION DES COLLISIONS ===")
    
    if navigation_grid is not None:
        print("  🗺️  Utilisation de A* pour trajectoires réalistes")
    else:
        print("  ⚠️  Trajectoires Manhattan simples (pas de grille)")
    
    agents_dict = {a['id']: a for a in agents}
    
    # === ASSIGNER CASES DE DÉPÔT UNIQUES ===
    # Cases de dépôt disponibles (autour de [6,5] - SANS le centre)
    AVAILABLE_DEPOTS = [
        [5, 4], [6, 4], [7, 4],
        [5, 5],         [7, 5],  # [6, 5] enlevé (c'est le centre de préparation)
        [5, 6], [6, 6], [7, 6]
    ]
    
    depot_assignments = {}  # {agent_id: [x, y]}
    used_depots = []
    
    print("\n  📦 Assignation des cases de dépôt :")
    for agent_id in solution['agents_routes'].keys():
        # Trouver une case de dépôt non utilisée
        available = [d for d in AVAILABLE_DEPOTS if d not in used_depots]
        
        if available:
            # Assigner la première case disponible
            assigned = available[0]
            depot_assignments[agent_id] = assigned
            used_depots.append(assigned)
            print(f"    {agent_id} → {assigned}")
        else:
            # Si toutes les cases sont prises, utiliser [6,5] par défaut
            depot_assignments[agent_id] = [6, 5]
            print(f"    {agent_id} → [6, 5] (défaut, toutes cases prises)")
    
    # Fonction pour recalculer les trajectoires
    def compute_all_trajectories(routes_with_delays):
        trajectories = {}
        all_depot_positions = {}
        
        for agent_id, route_data in routes_with_delays.items():
            agent = agents_dict[agent_id]
            products_route = route_data['products']
            start_delay = route_data.get('start_delay', 0)
            assigned_depot = depot_assignments.get(agent_id, [6, 5])
            
            trajectory, depot_positions = calculate_agent_trajectory(
                agent, products_route, entry_point, distance_data, 
                start_delay, navigation_grid, assigned_depot
            )
            trajectories[agent_id] = trajectory
            all_depot_positions[agent_id] = depot_positions
        
        return trajectories, all_depot_positions
    
    # Initialiser avec délai 0 pour tous
    routes_with_delays = {}
    for agent_id, route_data in solution['agents_routes'].items():
        routes_with_delays[agent_id] = {
            'products': route_data['products'],
            'start_delay': 0
        }
    
    # Itérations pour résoudre collisions
    for iteration in range(max_iterations):
        print(f"\n--- Itération {iteration + 1} ---")
        
        # Calculer trajectoires
        agents_trajectories, depot_positions_all = compute_all_trajectories(routes_with_delays)
        
        for agent_id, traj in agents_trajectories.items():
            delay = routes_with_delays[agent_id]['start_delay']
            print(f"{agent_id}: {len(traj)} min de trajet (délai départ: +{delay} min)")
        
        # Détecter collisions
        collisions = detect_collisions(agents_trajectories)
        
        print(f"🚨 Collisions: {len(collisions)}")
        
        if len(collisions) == 0:
            print("✅ Aucune collision !")
            break
        
        # Afficher quelques collisions
        for agent1, agent2, minute, pos in collisions[:5]:
            time_str = f"{9 + minute//60:02d}:{minute%60:02d}"
            print(f"  ⚠️  {agent1} ⚔️  {agent2} à {time_str} sur {pos}")
        
        # Ajustement : décaler l'agent avec le plus de collisions
        collision_counts = {}
        for agent1, agent2, _, _ in collisions:
            collision_counts[agent1] = collision_counts.get(agent1, 0) + 1
            collision_counts[agent2] = collision_counts.get(agent2, 0) + 1
        
        # Trouver l'agent le plus problématique
        most_colliding_agent = max(collision_counts, key=collision_counts.get)
        
        # Décaler de 2 minutes
        routes_with_delays[most_colliding_agent]['start_delay'] += 2
        print(f"  → Décalage de {most_colliding_agent} : +2 min (total: {routes_with_delays[most_colliding_agent]['start_delay']} min)")
    
    # Résultat final
    final_trajectories, final_depot_positions = compute_all_trajectories(routes_with_delays)
    final_collisions = detect_collisions(final_trajectories)
    
    print(f"\n=== RÉSULTAT FINAL ===")
    print(f"Collisions restantes: {len(final_collisions)}")
    
    return {
        'trajectories': final_trajectories,
        'collisions': final_collisions,
        'delays': {aid: rd['start_delay'] for aid, rd in routes_with_delays.items()},
        'depot_positions': final_depot_positions,  # Positions des dépôts par agent
        'depot_assignments': depot_assignments     # Assignation des cases de dépôt
    }

if __name__ == "__main__":
    from loader import load_warehouse, load_products, load_agents, load_orders
    from distances import calculate_distance_matrix
    from optimizer import optimize_routes
    
    # Charger les données
    warehouse = load_warehouse('warehouse.json')
    products = load_products('products.json')
    agents = load_agents('agents.json')
    orders = load_orders('orders.json')
    
    with open('zones_access.json', 'r') as f:
        zones_access = json.load(f)
    
    distance_data = calculate_distance_matrix(products, warehouse['entry_point'])
    
    # Optimiser (5 premières commandes)
    test_orders = orders[:5]
    solution = optimize_routes(test_orders, products, agents, distance_data, zones_access)
    
    # Vérifier collisions
    if solution['status'] == 'success':
        collision_result = check_and_adjust_collisions(
            solution, 
            agents, 
            warehouse['entry_point'], 
            distance_data
        )
