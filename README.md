cat > README.md << 'EOF'
# 🏭 OPTIPICK - Optimisation de Tournées d'Entrepôt

Système d'optimisation de tournées pour entrepôt utilisant **OR-Tools CP-SAT** et **A* pathfinding**.

## Fonctionnalités

- Optimisation multi-agents (robots, humains, chariots)
- Gestion des voyages multiples  
- Résolution des collisions entre agents
- Pathfinding A* avec évitement d'obstacles
- Interface Streamlit interactive
- Visualisation 2D des trajectoires
- Système de configuration des paramètres

## Installation
```bash
# Cloner le repo
git clone https://github.com/Msegura4/optimization_with_or_tool.git
cd optimization_with_or_tool

# Créer environnement virtuel
python3 -m venv env
source env/bin/activate

# Installer dépendances
pip install streamlit ortools matplotlib pandas numpy
```

## Utilisation
```bash
streamlit run app.py
```

Ouvre ton navigateur : **http://localhost:8501**

## Structure
```
optipick/
├── app.py                      # Interface Streamlit
├── optimizer_mintime.py        # Optimisation OR-Tools CP-SAT + implémentation de toutes les contraintes
├── collision_checker.py        # Résolution des collisions
├── distances.py                # Calcul distances avec A*
├── astar.py                    # Algorithme A* pathfinding
├── visualize_warehouse.py      # Visualisation 2D
├── run_optimization.py         # Orchestration
├── loader.py                   # Chargement données
├── default_params.json         # Configuration
├── agents.json                 # Définition des agents
├── warehouse.json              # Plan de l'entrepôt
├── products.json               # Catalogue produits
└── orders.json                 # Commandes à traiter
```

## Configuration

Paramètres configurables via l'onglet **⚙️ PARAMÈTRES** :
- Solver OR-Tools (threads, temps max, random seed)
- Gestion collisions (max_iterations = 250)
- Coûts horaires des agents
- Vitesses et capacités
- Dimensions de l'entrepôt

## Algorithmes

- **CP-SAT (OR-Tools)** : Optimisation globale des tournées
- **A\*** : Pathfinding avec évitement d'obstacles  
- **Résolution itérative** : Détection et ajustement des collisions

## Performance

- 10 commandes : ~45 secondes
- 20 commandes : ~120 secondes
- 40 commandes : ~300 secondes

## Technologies

- Python 3.9+
- OR-Tools (CP SAT)
- Streamlit
- Matplotlib
- Pandas
- NumPy
- A*

## 📝 Licence

Apache License 2.0

## 👤 Auteur

Math Segura
EOF