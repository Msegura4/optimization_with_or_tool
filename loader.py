import json

def load_warehouse(filepath):
    """Charge les données de l'entrepôt"""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_products(filepath):
    """Charge les données des produits"""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_agents(filepath):
    """Charge les données des agents"""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_orders(filepath):
    """Charge les données des commandes"""
    with open(filepath, 'r') as f:
        return json.load(f)

if __name__ == "__main__":
    # Charger les données
    warehouse = load_warehouse('warehouse.json')
    products = load_products('products.json')
    agents = load_agents('agents.json')
    orders = load_orders('orders.json')
    
    # Afficher des infos de vérification
    print("=== DONNÉES CHARGÉES ===")
    print(f"Entrepôt : {warehouse['dimensions']['width']}x{warehouse['dimensions']['height']}")
    print(f"Nombre de zones : {len(warehouse['zones'])}")
    print(f"Nombre de produits : {len(products)}")
    print(f"Nombre d'agents : {len(agents)}")
    print(f"Nombre de commandes : {len(orders)}")
    
    # Détails agents
    print("\n=== AGENTS ===")
    for agent in agents:
        print(f"{agent['id']} ({agent['type']}) - Capacité: {agent['capacity_weight']}kg, {agent['capacity_volume']}dm³")
    
    # Quelques produits
    print("\n=== EXEMPLES PRODUITS ===")
    for i in range(5):
        p = products[i]
        print(f"{p['id']}: {p['name']} - {p['category']} - {p['weight']}kg - Location: {p['location']} - pickup_location: {p['pickup_location']}")
    
    # Quelques commandes
    print("\n=== EXEMPLES COMMANDES ===")
    for i in range(3):
        o = orders[i]
        print(f"{o['id']} ({o['priority']}) - {len(o['items'])} articles - Deadline: {o['deadline']}")