"""
Module pour lancer l'optimisation OPTIPICK depuis Streamlit
Retourne les résultats structurés pour affichage
"""

import json
from loader import load_warehouse, load_products, load_agents, load_orders
from distances import calculate_distance_matrix
from optimizer_mintime import optimize_routes, minutes_to_time
from collision_checker import check_and_adjust_collisions


def run_optimization(num_orders=10, max_iterations=250):
    """
    Lance l'optimisation complète et retourne les résultats
    
    Args:
        num_orders: nombre de commandes à traiter
        max_iterations: nombre max d'itérations pour résoudre les collisions (défaut: 250)
    
    Returns:
        dict avec tous les résultats de l'optimisation
    """
    
    # === CHARGEMENT DES DONNÉES ===
    warehouse = load_warehouse('warehouse.json')
    products = load_products('products.json')
    agents = load_agents('agents.json')
    orders = load_orders('orders.json')
    
    with open('zones_access.json', 'r') as f:
        zones_access = json.load(f)
    
    # === CALCUL DES DISTANCES ===
    navigation_grid = warehouse.get('navigation_grid', None)
    distance_data = calculate_distance_matrix(products, warehouse['entry_point'], navigation_grid)
    
    # === SÉLECTION DES COMMANDES ===
    selected_orders = orders[:num_orders]
    
    # === OPTIMISATION OR-TOOLS ===
    solution = optimize_routes(
        selected_orders, 
        products, 
        agents, 
        distance_data, 
        zones_access,
        warehouse['entry_point']
    )
    
    if solution['status'] != 'success':
        return {'status': 'error', 'message': 'Échec de l\'optimisation'}
    
    # === VÉRIFICATION COLLISIONS ===
    collision_result = check_and_adjust_collisions(
        solution,
        agents,
        warehouse['entry_point'],
        distance_data,
        max_iterations=max_iterations,  # Utilise le paramètre passé à la fonction
        navigation_grid=navigation_grid
    )
    
    # === CALCUL DES STATISTIQUES ===
    agents_dict = {a['id']: a for a in agents}
    
    # Coûts horaires
    COST_RATES = {
        'robot': 5,    # 5€/h
        'human': 25,   # 25€/h
        'cart': 3      # 3€/h
    }
    
    total_cost = 0.0
    agent_stats = []
    
    for agent_id, route_data in solution['agents_routes'].items():
        agent = agents_dict[agent_id]
        products_list = route_data['products']
        delay = collision_result['delays'].get(agent_id, 0)
        
        if products_list:
            # Temps de travail
            last_visit = products_list[-1]['visit_time'] + delay
            start_time = delay
            duree_min = last_visit - start_time
            duree_heures = duree_min / 60.0
            
            # Coût
            agent_cost = duree_heures * COST_RATES[agent['type']]
            total_cost += agent_cost
            
            # Statistiques agent
            trips = {}
            for p in products_list:
                trip = p.get('trip_number', 1)
                trips[trip] = trips.get(trip, 0) + 1
            
            agent_stats.append({
                'id': agent_id,
                'type': agent['type'],
                'nb_produits': len(products_list),
                'nb_voyages': len(trips),
                'debut': minutes_to_time(start_time),
                'fin': minutes_to_time(last_visit),
                'duree_min': duree_min,
                'duree_heures': duree_heures,
                'cout': agent_cost,
                'delay': delay
            })
    
    # Ajouter coût des humains guidant les chariots
    if solution.get('human_cart_assignments'):
        for cart_id, human_id in solution['human_cart_assignments'].items():
            if cart_id in solution['agents_routes']:
                cart_route = solution['agents_routes'][cart_id]
                products_list = cart_route['products']
                delay = collision_result['delays'].get(cart_id, 0)
                
                if products_list:
                    last_visit = products_list[-1]['visit_time'] + delay
                    start_time = delay
                    duree_heures = (last_visit - start_time) / 60.0
                    human_cost = duree_heures * COST_RATES['human']
                    total_cost += human_cost
    
    # Temps global
    max_end_time = 0
    for agent_id, route_data in solution['agents_routes'].items():
        products_list = route_data['products']
        delay = collision_result['delays'].get(agent_id, 0)
        if products_list:
            last_visit = products_list[-1]['visit_time'] + delay
            max_end_time = max(max_end_time, last_visit)
    
    temps_global_str = f"{max_end_time} min"
    if max_end_time >= 60:
        heures = max_end_time // 60
        minutes = max_end_time % 60
        temps_global_str = f"{heures}h{minutes:02d}"
    
    # Totaux
    total_products = sum(len(r['products']) for r in solution['agents_routes'].values())
    total_voyages = sum(len(set(p.get('trip_number', 1) for p in r['products'])) for r in solution['agents_routes'].values())
    total_collisions = len(collision_result['collisions'])
    
    # === RETOUR STRUCTURÉ ===
    return {
        'status': 'success',
        'num_orders': num_orders,
        'total_products': total_products,
        'agents_used': len(solution['agents_routes']),
        'total_voyages': total_voyages,
        'temps_global_str': temps_global_str,
        'temps_global_min': max_end_time,
        'total_cost': total_cost,
        'cost_per_order': total_cost / num_orders if num_orders > 0 else 0,
        'cost_per_agent': total_cost / len(solution['agents_routes']) if len(solution['agents_routes']) > 0 else 0,
        'total_collisions': total_collisions,
        'agent_stats': sorted(agent_stats, key=lambda x: x['duree_min'], reverse=True),
        'solution': solution,
        'collision_result': collision_result,
        'warehouse': warehouse,
        'agents': agents,
        'distance_data': distance_data
    }


if __name__ == "__main__":
    # Test du module
    print("=== TEST RUN_OPTIMIZATION ===")
    result = run_optimization(5)
    
    if result['status'] == 'success':
        print(f"\n✓ Optimisation réussie")
        print(f"  Commandes : {result['num_orders']}")
        print(f"  Produits : {result['total_products']}")
        print(f"  Agents : {result['agents_used']}")
        print(f"  Temps : {result['temps_global_str']}")
        print(f"  Coût : {result['total_cost']:.2f}€")
        print(f"  Collisions : {result['total_collisions']}")
    else:
        print(f"\n❌ Erreur : {result.get('message')}")
