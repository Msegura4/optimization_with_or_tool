"""
OPTIPICK - Optimisation de Tournées d'Entrepôt
Workflow principal avec VOYAGES MULTIPLES
"""

import json

def main():
    """
    Workflow principal OPTIPICK avec voyages multiples
    
    1. Charger les données
    2. Calculer distances
    3. Optimiser les tournées (OR-Tools avec voyages multiples)
    4. Vérifier et ajuster les collisions
    5. Afficher résultats finaux
    """
    
    print("="*80)
    print("                    OPTIPICK WORKFLOW - OPTIMISATION TEMPS")
    print("="*80)
    
    # Importer les modules nécessaires
    from optimizer_mintime import optimize_routes, minutes_to_time, time_to_minutes
    from loader import load_warehouse, load_products, load_agents, load_orders
    from distances import calculate_distance_matrix
    from collision_checker import check_and_adjust_collisions
    
    # === ÉTAPE 1 : CHARGEMENT DES DONNÉES ===
    print("\n[1/5] Chargement des données...")
    
    warehouse = load_warehouse('warehouse.json')
    products = load_products('products.json')
    agents = load_agents('agents.json')
    orders = load_orders('orders.json')
    
    with open('zones_access.json', 'r') as f:
        zones_access = json.load(f)
    
    print(f"  ✓ Entrepôt : {warehouse['dimensions']['width']}x{warehouse['dimensions']['height']}")
    print(f"  ✓ Produits : {len(products)}")
    print(f"  ✓ Agents : {len(agents)}")
    print(f"  ✓ Commandes disponibles : {len(orders)}")
    
    # === CHOIX DU NOMBRE DE COMMANDES ===
    print("\n>>> NOMBRE DE COMMANDES À TRAITER <<<")
    while True:
        try:
            choix_nb = input(f"Combien de commandes traiter ? (1-{len(orders)}) : ").strip()
            num_orders = int(choix_nb)
            
            if 1 <= num_orders <= len(orders):
                print(f"✓ {num_orders} commandes sélectionnées\n")
                break
            else:
                print(f"❌ Entrez un nombre entre 1 et {len(orders)}")
        except ValueError:
            print("❌ Entrez un nombre valide")
    
    # === ÉTAPE 2 : CALCUL DES DISTANCES ===
    print("\n[2/5] Calcul de la matrice des distances...")
    
    # Charger la grille de navigation
    navigation_grid = warehouse.get('navigation_grid', None)
    
    if navigation_grid:
        print(f"  🗺️  Grille de navigation chargée ({len(navigation_grid)}x{len(navigation_grid[0])})")
    else:
        print(f"  ⚠️  Pas de grille de navigation → distances approximatives")
    
    distance_data = calculate_distance_matrix(products, warehouse['entry_point'], navigation_grid)
    print(f"  ✓ {len(distance_data['distances'])} distances calculées")
    
    # === ÉTAPE 3 : OPTIMISATION OR-TOOLS ===
    print(f"\n[3/5] Optimisation des tournées - Stratégie : MINIMISER LE TEMPS...")
    
    selected_orders = orders[:num_orders]
    
    solution = optimize_routes(
        selected_orders, 
        products, 
        agents, 
        distance_data, 
        zones_access,
        warehouse['entry_point']
    )
    
    if solution['status'] != 'success':
        print("  ❌ Échec de l'optimisation")
        return
    
    print(f"  ✓ Tournées optimisées pour {len(solution['agents_routes'])} agents")
    
    # === ÉTAPE 4 : VÉRIFICATION ET RÉSOLUTION DES COLLISIONS ===
    print("\n[4/5] Vérification et résolution des collisions...")
    
    collision_result = check_and_adjust_collisions(
        solution,
        agents,
        warehouse['entry_point'],
        distance_data,
        max_iterations=100,  # Augmenté pour gérer cas complexes (7-8 agents)
        navigation_grid=navigation_grid
    )
    
    # === ÉTAPE 5 : RÉSULTATS FINAUX ===
    print("\n" + "="*80)
    print(f"                RÉSULTATS FINAUX - OPTIMISATION TEMPS")
    print("="*80)
    
    # Afficher les assignations humain→chariot
    if solution.get('human_cart_assignments'):
        print("\n>>> ASSIGNATIONS HUMAIN→CHARIOT <<<")
        for cart_id, human_id in solution['human_cart_assignments'].items():
            print(f"  {cart_id} guidé par {human_id}")
    
    # Afficher les tournées avec délais et voyages
    print("\n>>> TOURNÉES AVEC VOYAGES MULTIPLES <<<")
    
    agents_dict = {a['id']: a for a in agents}
    
    for agent_id, route_data in solution['agents_routes'].items():
        agent = agents_dict[agent_id]
        products_list = route_data['products']
        delay = collision_result['delays'].get(agent_id, 0)
        
        # Calculer temps total de trajet
        trajectory = collision_result['trajectories'].get(agent_id, {})
        temps_trajet_min = len(trajectory)
        temps_trajet_str = f"{temps_trajet_min} min"
        if temps_trajet_min >= 60:
            heures = temps_trajet_min // 60
            minutes = temps_trajet_min % 60
            temps_trajet_str = f"{heures}h{minutes:02d}"
        
        # Grouper par voyage
        trips = {}
        for p in products_list:
            trip = p.get('trip_number', 1)
            if trip not in trips:
                trips[trip] = []
            trips[trip].append(p)
        
        print(f"\n{agent_id} ({agent['type']}) - Délai départ: +{delay} min | Temps trajet: {temps_trajet_str}")
        print(f"  Poids total: {route_data['total_weight']:.1f} kg / {agent['capacity_weight']} kg")
        print(f"  Volume total: {route_data['total_volume']} dm³ / {agent['capacity_volume']} dm³")
        print(f"  Produits : {len(products_list)} | Voyages : {len(trips)}")
        
        # Afficher chaque voyage (limiter à 3 voyages max pour pas surcharger l'affichage)
        for trip_num in sorted(trips.keys())[:3]:
            trip_products = trips[trip_num]
            trip_weight = sum(p['product_data']['weight'] for p in trip_products)
            trip_volume = sum(p['product_data']['volume'] for p in trip_products)
            print(f"\n    🚚 Voyage {trip_num} : {len(trip_products)} produits | {trip_weight:.1f}kg | {trip_volume}dm³")
            
            # Afficher produits du voyage (max 5 premiers)
            for idx, p in enumerate(trip_products[:5]):
                visit_mins = p['visit_time'] + delay
                visit_time_str = minutes_to_time(visit_mins)
                deadline_str = p['deadline']
                priority = p['priority']
                priority_icon = "⚡" if priority == "express" else "📦"
                
                deadline_mins = time_to_minutes(deadline_str)
                status = "✓" if visit_mins <= deadline_mins else "❌ RETARD"
                
                print(f"      {priority_icon} {p['product_id']} - {visit_time_str} | Deadline: {deadline_str} {status}")
            
            if len(trip_products) > 5:
                print(f"      ... et {len(trip_products) - 5} autres produits")
        
        if len(trips) > 3:
            print(f"\n    ... et {len(trips) - 3} autres voyages")
    
    # ANALYSE DISTRIBUTION DES CHARGES
    print("\n>>> ANALYSE DISTRIBUTION <<<")
    agent_stats = []
    
    for agent_id, route_data in solution['agents_routes'].items():
        products_list = route_data['products']
        delay = collision_result['delays'].get(agent_id, 0)
        
        # Compter le nombre de voyages
        trips = {}
        for p in products_list:
            trip = p.get('trip_number', 1)
            trips[trip] = trips.get(trip, 0) + 1
        
        if products_list:
            last_visit = products_list[-1]['visit_time'] + delay
            start_time = delay
            duree_travail = last_visit - start_time
            
            agent_stats.append({
                'id': agent_id,
                'nb_produits': len(products_list),
                'nb_voyages': len(trips),
                'debut': minutes_to_time(start_time),
                'fin': minutes_to_time(last_visit),
                'duree': duree_travail
            })
    
    # Trier par durée décroissante
    agent_stats.sort(key=lambda x: x['duree'], reverse=True)
    
    print(f"\n  {'Agent':<6} | {'Produits':<9} | {'Voyages':<8} | {'Début':<8} | {'Fin':<8} | {'Durée':<10}")
    print(f"  {'-'*6}-+-{'-'*9}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*10}")
    
    for stat in agent_stats:
        duree_str = f"{stat['duree']} min"
        if stat['duree'] >= 60:
            h = stat['duree'] // 60
            m = stat['duree'] % 60
            duree_str = f"{h}h{m:02d}"
        
        print(f"  {stat['id']:<6} | {stat['nb_produits']:<9} | {stat['nb_voyages']:<8} | {stat['debut']:<8} | {stat['fin']:<8} | {duree_str:<10}")
    
    # Agent le plus lent (goulot d'étranglement)
    if agent_stats:
        bottleneck = agent_stats[0]
        print(f"\n  ⚠️  GOULOT D'ÉTRANGLEMENT : {bottleneck['id']} avec {bottleneck['nb_produits']} produits en {bottleneck['nb_voyages']} voyages")
        print(f"      → Termine à {bottleneck['fin']} (durée: {bottleneck['duree']} min)")
    
    # Résumé collisions
    print("\n>>> RÉSUMÉ COLLISIONS <<<")
    print(f"  Collisions résolues : {len(collision_result['collisions'])} collisions restantes")
    if len(collision_result['collisions']) > 0:
        print("  ⚠️  Quelques collisions subsistent, augmenter max_iterations")
    else:
        print("  ✅ Toutes les collisions résolues !")
    
    # Résumé global
    total_products = sum(len(r['products']) for r in solution['agents_routes'].values())
    total_temps_trajet = sum(len(traj) for traj in collision_result['trajectories'].values())
    total_voyages = sum(len(set(p.get('trip_number', 1) for p in r['products'])) for r in solution['agents_routes'].values())
    
    # Calculer le temps global (quand le dernier agent termine)
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
    
    # Calculer le coût global
    # Coûts horaires par type d'agent
    COST_RATES = {
        'robot': 5,    # 5€/h
        'human': 25,   # 25€/h
        'cart': 3      # 3€/h
    }
    
    total_cost = 0.0
    for agent_id, route_data in solution['agents_routes'].items():
        agent = agents_dict[agent_id]
        products_list = route_data['products']
        delay = collision_result['delays'].get(agent_id, 0)
        
        if products_list:
            # Temps de travail = fin - début (en minutes)
            last_visit = products_list[-1]['visit_time'] + delay
            start_time = delay
            duree_min = last_visit - start_time
            
            # Convertir en heures
            duree_heures = duree_min / 60.0
            
            # Coût = durée × coût horaire
            agent_cost = duree_heures * COST_RATES[agent['type']]
            total_cost += agent_cost
    
    # Ajouter le coût des humains qui guident les chariots
    if solution.get('human_cart_assignments'):
        for cart_id, human_id in solution['human_cart_assignments'].items():
            # Si le chariot est utilisé, ajouter le coût de l'humain qui le guide
            if cart_id in solution['agents_routes']:
                cart_route = solution['agents_routes'][cart_id]
                products_list = cart_route['products']
                delay = collision_result['delays'].get(cart_id, 0)
                
                if products_list:
                    last_visit = products_list[-1]['visit_time'] + delay
                    start_time = delay
                    duree_min = last_visit - start_time
                    duree_heures = duree_min / 60.0
                    
                    # Coût humain
                    human_cost = duree_heures * COST_RATES['human']
                    total_cost += human_cost
    
    print(f"\n>>> RÉSUMÉ GLOBAL <<<")
    print(f"  Stratégie : MINIMISER LE TEMPS")
    print(f"  Commandes traitées : {num_orders}")
    print(f"  Produits ramassés : {total_products}")
    print(f"  Agents utilisés : {len(solution['agents_routes'])}")
    print(f"  Voyages totaux : {total_voyages}")
    print(f"  Temps global (début → fin) : {temps_global_str}")
    print(f"  Temps total de trajet : {total_temps_trajet} min (cumulé tous agents)")
    print(f"  Délais appliqués : {sum(collision_result['delays'].values())} min au total")
    print(f"  💰 Coût total : {total_cost:.2f}€")
    
    print("\n" + "="*80)
    print("                      WORKFLOW TERMINÉ")
    print("="*80)
    
    return {
        'solution': solution,
        'collision_result': collision_result,
        'warehouse': warehouse,
        'agents': agents
    }

if __name__ == "__main__":
    result = main()