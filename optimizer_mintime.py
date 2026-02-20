import json
from ortools.sat.python import cp_model
from loader import load_warehouse, load_products, load_agents, load_orders
from distances import calculate_distance_matrix

def time_to_minutes(time_str):
    """Convertit heure 'HH:MM' en minutes depuis 9h00"""
    hours, minutes = map(int, time_str.split(':'))
    total_minutes = hours * 60 + minutes
    return total_minutes - (9 * 60)

def minutes_to_time(minutes):
    """Convertit minutes depuis 9h00 en heure 'HH:MM'"""
    total_minutes = minutes + (9 * 60)
    hours = total_minutes // 60
    mins = total_minutes % 60
    return f"{hours:02d}:{mins:02d}"

def can_agent_handle_product(agent, product, zones_access):
    """Vérifie si un agent peut gérer un produit selon les contraintes"""
    if agent['type'] == 'robot':
        restrictions = agent.get('restrictions', {})
        product_location = product['location']
        if product_location not in zones_access['robot_accessible_storage']:
            return False
        if product['category'] == 'food':
            return False
        if restrictions.get('no_fragile', False) and product.get('fragile', False):
            return False
        max_weight = restrictions.get('max_item_weight', float('inf'))
        if product['weight'] > max_weight:
            return False
    return True

def optimize_routes(available_orders, products, agents, distance_data, zones_access, entry_point, current_time="08:00"):
    """
    Optimise les tournées AVEC VOYAGES MULTIPLES
    Les agents peuvent retourner à la zone de préparation [6,5] pour déposer et repartir
    """
    
    model = cp_model.CpModel()
    
    # Point de préparation où les agents déposent les produits
    PREPARATION_POINT = [6, 5]  # Zone verte de préparation
    
    # === DONNÉES ===
    products_to_pick = []
    product_dict = {p['id']: p for p in products}
    
    for order in available_orders:
        for item in order['items']:
            prod_id = item['product_id']
            quantity = item['quantity']
            for _ in range(quantity):
                products_to_pick.append({
                    'product_id': prod_id,
                    'order_id': order['id'],
                    'product_data': product_dict[prod_id],
                    'deadline': order['deadline'],
                    'priority': order['priority']
                })
    
    num_products = len(products_to_pick)
    num_agents = len(agents)
    MAX_TRIPS = 15  # Maximum de voyages par agent
    
    print(f"\n=== OPTIMISATION MULTI-VOYAGES ===")
    print(f"Produits à ramasser : {num_products}")
    print(f"Agents disponibles : {num_agents}")
    print(f"Voyages max par agent : {MAX_TRIPS}")
    
    # === VARIABLES ===
    
    TIME_START = 0
    TIME_END = 480
    
    # 1. Assignation produit → agent
    assignment = {}
    for i in range(num_products):
        for a in range(num_agents):
            if can_agent_handle_product(agents[a], products_to_pick[i]['product_data'], zones_access):
                assignment[(i, a)] = model.NewBoolVar(f'assign_p{i}_a{a}')
            else:
                assignment[(i, a)] = 0
    
    # 2. Numéro de voyage pour chaque produit (1 à MAX_TRIPS)
    trip_number = {}
    for i in range(num_products):
        for a in range(num_agents):
            if (i, a) in assignment and not isinstance(assignment[(i, a)], int):
                trip_number[(i, a)] = model.NewIntVar(1, MAX_TRIPS, f'trip_p{i}_a{a}')
    
    # 3. Temps de visite
    visit_time = {}
    for i in range(num_products):
        visit_time[i] = model.NewIntVar(TIME_START, TIME_END, f'visit_time_p{i}')
    
    # 4. Ordre de visite entre produits
    before = {}
    for a in range(num_agents):
        for i in range(num_products):
            for j in range(num_products):
                if i != j:
                    before[(i, j, a)] = model.NewBoolVar(f'before_p{i}_p{j}_a{a}')
    
    # C1b : Cohérence temporelle - Temps de trajet + picking
    PICKING_TIME = 1  # minutes
    METERS_PER_CELL = 3  # 1 case = 5 mètres
    
    for a in range(num_agents):
        agent = agents[a]
        agent_speed_m_per_min = agent['speed'] * 60
        
        for i in range(num_products):
            for j in range(num_products):
                if i != j and (i, a) in assignment and (j, a) in assignment:
                    var_i = assignment[(i, a)]
                    var_j = assignment[(j, a)]
                    
                    if not isinstance(var_i, int) and not isinstance(var_j, int):
                        # Si les deux produits assignés au même agent
                        both_assigned = model.NewBoolVar(f'both_p{i}_p{j}_a{a}')
                        model.Add(var_i + var_j == 2).OnlyEnforceIf(both_assigned)
                        model.Add(var_i + var_j < 2).OnlyEnforceIf(both_assigned.Not())
                        
                        # Si même agent, définir ordre
                        model.Add(before[(i, j, a)] + before[(j, i, a)] == 1).OnlyEnforceIf(both_assigned)
                        
                        # Si i avant j, calculer temps
                        prod_i_id = products_to_pick[i]['product_id']
                        prod_j_id = products_to_pick[j]['product_id']
                        
                        distance_cases = distance_data['distances'].get((prod_i_id, prod_j_id), 0)
                        distance_meters = distance_cases * METERS_PER_CELL
                        travel_time = int(distance_meters / agent_speed_m_per_min) + 1
                        
                        # Si même voyage, ajouter temps trajet + picking
                        same_trip = model.NewBoolVar(f'same_trip_p{i}_p{j}_a{a}')
                        if (i, a) in trip_number and (j, a) in trip_number:
                            model.Add(trip_number[(i, a)] == trip_number[(j, a)]).OnlyEnforceIf([both_assigned, same_trip])
                            model.Add(trip_number[(i, a)] != trip_number[(j, a)]).OnlyEnforceIf([both_assigned, same_trip.Not()])
                            
                            # Si même voyage ET i avant j
                            model.Add(visit_time[j] >= visit_time[i] + travel_time + PICKING_TIME).OnlyEnforceIf([before[(i, j, a)], same_trip])
                            
                            # Si voyages différents ET i avant j : retour à préparation [6,5]
                            # Temps = distance(i → préparation) + 2 min dépôt + distance(préparation → j)
                            prod_i_loc = products_to_pick[i]['product_data']['pickup_location']
                            prod_j_loc = products_to_pick[j]['product_data']['pickup_location']
                            
                            # Distance Manhattan produit i → [6,5]
                            dist_to_prep = abs(prod_i_loc[0] - PREPARATION_POINT[0]) + abs(prod_i_loc[1] - PREPARATION_POINT[1])
                            time_to_prep = int((dist_to_prep * METERS_PER_CELL) / agent_speed_m_per_min) + 1
                            
                            # Distance Manhattan [6,5] → produit j
                            dist_from_prep = abs(PREPARATION_POINT[0] - prod_j_loc[0]) + abs(PREPARATION_POINT[1] - prod_j_loc[1])
                            time_from_prep = int((dist_from_prep * METERS_PER_CELL) / agent_speed_m_per_min) + 1
                            
                            # Temps total retour = aller + dépôt + retour
                            DEPOT_TIME = 2  # minutes pour déposer
                            return_time = time_to_prep + DEPOT_TIME + time_from_prep
                            
                            model.Add(visit_time[j] >= visit_time[i] + return_time + PICKING_TIME).OnlyEnforceIf([before[(i, j, a)], same_trip.Not()])
    
    # === CONTRAINTES ===
    
    # C1 : Chaque produit assigné à exactement 1 agent
    for i in range(num_products):
        valid = [assignment[(i, a)] for a in range(num_agents) if (i, a) in assignment and not isinstance(assignment[(i, a)], int)]
        if valid:
            model.Add(sum(valid) == 1)
    
    # C1b : FORCER l'utilisation des robots pour produits zone robot
    # Si un produit est en zone robot, il DOIT être assigné à un robot
    robot_indices = [a for a, agent in enumerate(agents) if agent['type'] == 'robot']
    
    for i in range(num_products):
        product_location = products_to_pick[i]['product_data']['location']
        
        # Si produit en zone robot
        if product_location in zones_access['robot_accessible_storage']:
            # Ce produit DOIT être pris par un robot
            robot_assignments = [
                assignment[(i, a)] 
                for a in robot_indices 
                if (i, a) in assignment and not isinstance(assignment[(i, a)], int)
            ]
            
            if robot_assignments:
                # Au moins un robot doit le prendre (en fait exactement 1 grâce à C1)
                model.Add(sum(robot_assignments) == 1)
    
    # C2 : Capacité POIDS par voyage
    for a in range(num_agents):
        agent = agents[a]
        for trip in range(1, MAX_TRIPS + 1):
            # Poids total des produits du voyage 'trip' pour agent 'a'
            trip_weight = []
            for i in range(num_products):
                if (i, a) in assignment and not isinstance(assignment[(i, a)], int):
                    # Indicateur : ce produit est dans ce voyage ?
                    in_this_trip = model.NewBoolVar(f'p{i}_a{a}_trip{trip}')
                    
                    # in_this_trip = 1 si (produit assigné à 'a' ET trip_number == trip)
                    model.Add(trip_number[(i, a)] == trip).OnlyEnforceIf([assignment[(i, a)], in_this_trip])
                    model.Add(trip_number[(i, a)] != trip).OnlyEnforceIf([assignment[(i, a)], in_this_trip.Not()])
                    model.Add(in_this_trip == 0).OnlyEnforceIf(assignment[(i, a)].Not())
                    
                    weight_g = int(products_to_pick[i]['product_data']['weight'] * 1000)
                    trip_weight.append(weight_g * in_this_trip)
            
            if trip_weight:
                capacity_g = int(agent['capacity_weight'] * 1000)
                model.Add(sum(trip_weight) <= capacity_g)
    
    # C3 : Capacité VOLUME par voyage
    for a in range(num_agents):
        agent = agents[a]
        for trip in range(1, MAX_TRIPS + 1):
            trip_volume = []
            for i in range(num_products):
                if (i, a) in assignment and not isinstance(assignment[(i, a)], int):
                    in_this_trip = model.NewBoolVar(f'p{i}_a{a}_trip{trip}_vol')
                    
                    model.Add(trip_number[(i, a)] == trip).OnlyEnforceIf([assignment[(i, a)], in_this_trip])
                    model.Add(trip_number[(i, a)] != trip).OnlyEnforceIf([assignment[(i, a)], in_this_trip.Not()])
                    model.Add(in_this_trip == 0).OnlyEnforceIf(assignment[(i, a)].Not())
                    
                    volume = int(products_to_pick[i]['product_data']['volume'])
                    trip_volume.append(volume * in_this_trip)
            
            if trip_volume:
                model.Add(sum(trip_volume) <= agent['capacity_volume'])
    
    # C4 : Incompatibilités produits (même voyage seulement)
    for i in range(num_products):
        for j in range(i + 1, num_products):
            prod_i = products_to_pick[i]['product_data']
            prod_j = products_to_pick[j]['product_data']
            
            incompatible_ids = prod_i.get('incompatible_with', [])
            if prod_j['id'] in incompatible_ids:
                for a in range(num_agents):
                    if (i, a) in assignment and (j, a) in assignment:
                        var_i = assignment[(i, a)]
                        var_j = assignment[(j, a)]
                        if not isinstance(var_i, int) and not isinstance(var_j, int):
                            # Si même agent ET même voyage → interdit
                            both_same = model.NewBoolVar(f'incomp_p{i}_p{j}_a{a}')
                            model.Add(var_i + var_j == 2).OnlyEnforceIf(both_same)
                            model.Add(var_i + var_j < 2).OnlyEnforceIf(both_same.Not())
                            
                            same_trip = model.NewBoolVar(f'same_trip_p{i}_p{j}_a{a}')
                            model.Add(trip_number[(i, a)] == trip_number[(j, a)]).OnlyEnforceIf([both_same, same_trip])
                            model.Add(trip_number[(i, a)] != trip_number[(j, a)]).OnlyEnforceIf([both_same, same_trip.Not()])
                            
                            # Interdit d'être dans le même voyage
                            model.Add(same_trip == 0).OnlyEnforceIf(both_same)
    
    # C5 : Deadlines
    for i, product_item in enumerate(products_to_pick):
        deadline_minutes = time_to_minutes(product_item['deadline'])
        model.Add(visit_time[i] <= deadline_minutes)
    
    # C5b : Priority - Express avant Standard
    # Si un agent a des produits express ET standard, les express doivent être visités en premier
    for a in range(num_agents):
        for i in range(num_products):
            for j in range(num_products):
                if i != j:
                    prod_i = products_to_pick[i]
                    prod_j = products_to_pick[j]
                    
                    # Si i = express et j = standard, et assignés au même agent
                    if prod_i['priority'] == 'express' and prod_j['priority'] == 'standard':
                        if (i, a) in assignment and (j, a) in assignment:
                            var_i = assignment[(i, a)]
                            var_j = assignment[(j, a)]
                            
                            if not isinstance(var_i, int) and not isinstance(var_j, int):
                                # Si les deux sont assignés à l'agent a, alors i doit être visité avant j
                                both_assigned = model.NewBoolVar(f'both_express_std_p{i}_p{j}_a{a}')
                                model.Add(var_i + var_j == 2).OnlyEnforceIf(both_assigned)
                                model.Add(var_i + var_j < 2).OnlyEnforceIf(both_assigned.Not())
                                
                                # Si les deux assignés, express avant standard
                                model.Add(visit_time[i] < visit_time[j]).OnlyEnforceIf(both_assigned)
    
    # C6 : Agents utilisés + Chariots nécessitent humains
    agents_used = []
    for a in range(num_agents):
        agent_used = model.NewBoolVar(f'agent_{a}_used')
        products_assigned = [assignment[(i, a)] for i in range(num_products) if (i, a) in assignment and not isinstance(assignment[(i, a)], int)]
        if products_assigned:
            model.Add(sum(products_assigned) >= 1).OnlyEnforceIf(agent_used)
            model.Add(sum(products_assigned) == 0).OnlyEnforceIf(agent_used.Not())
        agents_used.append(agent_used)
    
    cart_indices = [i for i, agent in enumerate(agents) if agent['type'] == 'cart']
    human_indices = [i for i, agent in enumerate(agents) if agent['type'] == 'human']
    
    human_to_cart = {}
    for c_idx in cart_indices:
        for h_idx in human_indices:
            human_to_cart[(h_idx, c_idx)] = model.NewBoolVar(f'human_{h_idx}_to_cart_{c_idx}')
    
    for c_idx in cart_indices:
        cart_used = agents_used[c_idx]
        humans_assigned = [human_to_cart[(h_idx, c_idx)] for h_idx in human_indices]
        model.Add(sum(humans_assigned) == 1).OnlyEnforceIf(cart_used)
        model.Add(sum(humans_assigned) == 0).OnlyEnforceIf(cart_used.Not())
    
    for h_idx in human_indices:
        carts_assigned = [human_to_cart[(h_idx, c_idx)] for c_idx in cart_indices]
        model.Add(sum(carts_assigned) <= 1)
    
    # === OBJECTIF : MINIMISER LE TEMPS GLOBAL ===
    # Temps max = quand le dernier agent termine
    
    max_end_time = model.NewIntVar(TIME_START, TIME_END, 'max_end_time')
    
    # Pour chaque agent, trouver son temps de fin
    for a in range(num_agents):
        # Temps du dernier produit assigné à cet agent
        agent_last_time = model.NewIntVar(TIME_START, TIME_END, f'last_time_a{a}')
        
        # Trouver le max des visit_time pour cet agent
        products_times = []
        for i in range(num_products):
            if (i, a) in assignment and not isinstance(assignment[(i, a)], int):
                # Si produit assigné à cet agent
                time_contrib = model.NewIntVar(TIME_START, TIME_END, f'time_contrib_p{i}_a{a}')
                model.Add(time_contrib == visit_time[i]).OnlyEnforceIf(assignment[(i, a)])
                model.Add(time_contrib == TIME_START).OnlyEnforceIf(assignment[(i, a)].Not())
                products_times.append(time_contrib)
        
        if products_times:
            model.AddMaxEquality(agent_last_time, products_times)
        else:
            model.Add(agent_last_time == TIME_START)
        
        # max_end_time doit être >= au temps de fin de chaque agent
        model.Add(max_end_time >= agent_last_time)
    
    # OBJECTIF : Minimiser le temps global
    model.Minimize(max_end_time)
    
    # === RÉSOLUTION ===
    solver = cp_model.CpSolver()
    
    # PARAMÈTRES POUR RÉSULTATS COHÉRENTS ET OPTIMAUX
    solver.parameters.random_seed = 12345  # Résultats reproductibles
    solver.parameters.num_search_workers = 9  # Parallélisme (plus de threads)
    
    # Temps de résolution adapté au nombre de commandes
    num_orders = len(available_orders)
    
    if num_orders <= 20:
        solver.parameters.max_time_in_seconds = 45.0  # 45 sec
        print(f"  ⏱️  Temps de résolution : 45 sec (1-20 commandes)")
    elif num_orders <= 50:
        solver.parameters.max_time_in_seconds = 120.0  # 2 min
        print(f"  ⏱️  Temps de résolution : 2 min (21-50 commandes)")
    else:  # 51-100 commandes
        solver.parameters.max_time_in_seconds = 300.0  # 5 min
        print(f"  ⏱️  Temps de résolution : 5 min (51+ commandes)")
    
    status = solver.Solve(model)
    
    # === RÉSULTATS ===
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"\n=== SOLUTION TROUVÉE ===")
        print(f"Status: {'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE'}")
        
        result = {
            'status': 'success',
            'agents_routes': {},
            'human_cart_assignments': {}
        }
        
        # Extraire assignations humain→chariot
        for c_idx in cart_indices:
            for h_idx in human_indices:
                if solver.Value(human_to_cart[(h_idx, c_idx)]) == 1:
                    result['human_cart_assignments'][agents[c_idx]['id']] = agents[h_idx]['id']
        
        # Extraire les tournées par agent et par voyage
        for a in range(num_agents):
            assigned_products = []
            for i in range(num_products):
                if (i, a) in assignment and not isinstance(assignment[(i, a)], int):
                    if solver.Value(assignment[(i, a)]) == 1:
                        product_info = products_to_pick[i].copy()
                        product_info['visit_time'] = solver.Value(visit_time[i])
                        product_info['trip_number'] = solver.Value(trip_number[(i, a)])
                        assigned_products.append(product_info)
            
            if assigned_products:
                # Trier par numéro de voyage puis par temps de visite
                assigned_products.sort(key=lambda p: (p['trip_number'], p['visit_time']))
                
                result['agents_routes'][agents[a]['id']] = {
                    'agent': agents[a],
                    'products': assigned_products,
                    'total_weight': sum(p['product_data']['weight'] for p in assigned_products),
                    'total_volume': sum(p['product_data']['volume'] for p in assigned_products)
                }
        
        return result
    else:
        print(f"\n=== PAS DE SOLUTION ===")
        print(f"Status: {status}")
        return {'status': 'no_solution'}

if __name__ == "__main__":
    warehouse = load_warehouse('warehouse.json')
    products = load_products('products.json')
    agents = load_agents('agents.json')
    orders = load_orders('orders.json')
    
    with open('zones_access.json', 'r') as f:
        zones_access = json.load(f)
    
    distance_data = calculate_distance_matrix(products, warehouse['entry_point'])
    
    test_orders = orders[:10]
    
    solution = optimize_routes(
        test_orders, 
        products, 
        agents, 
        distance_data, 
        zones_access,
        warehouse['entry_point']
    )
    
    if solution['status'] == 'success':
        print("\n=== RÉSULTATS ===")
        for agent_id, route_data in solution['agents_routes'].items():
            print(f"\n{agent_id}:")
            print(f"  Total produits: {len(route_data['products'])}")
            
            # Grouper par voyage
            trips = {}
            for p in route_data['products']:
                trip = p['trip_number']
                if trip not in trips:
                    trips[trip] = []
                trips[trip].append(p)
            
            print(f"  Nombre de voyages: {len(trips)}")
            for trip_num in sorted(trips.keys()):
                trip_products = trips[trip_num]
                trip_weight = sum(p['product_data']['weight'] for p in trip_products)
                trip_volume = sum(p['product_data']['volume'] for p in trip_products)
                print(f"    Voyage {trip_num}: {len(trip_products)} produits, {trip_weight:.1f}kg, {trip_volume}dm³")