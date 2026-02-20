"""
OPTIPICK - Interface Streamlit
Visualisation et statistiques des tournées optimisées
AVEC SYSTÈME DE GESTION DES PARAMÈTRES
"""

import streamlit as st
import json
import sys
import os
from run_optimization import run_optimization

# === GESTION DES PARAMÈTRES PAR DÉFAUT ===
DEFAULT_PARAMS_FILE = 'default_params.json'

def load_default_params():
    """Charge les paramètres par défaut depuis le fichier JSON"""
    if os.path.exists(DEFAULT_PARAMS_FILE):
        with open(DEFAULT_PARAMS_FILE, 'r') as f:
            return json.load(f)
    else:
        # Fallback si fichier absent
        return {
            "solver": {
                "random_seed": 12345,
                "num_search_workers": 9,
                "max_time_seconds": 120
            },
            "collision": {
                "max_iterations": 250,
                "depot_time_minutes": 2
            },
            "costs": {
                "robot_per_hour": 5.0,
                "human_per_hour": 25.0,
                "cart_per_hour": 3.0
            },
            "agents": {
                "robot": {"capacity_weight": 20, "capacity_volume": 30, "speed": 2.0},
                "human": {"capacity_weight": 35, "capacity_volume": 50, "speed": 1.5},
                "cart": {"capacity_weight": 50, "capacity_volume": 80, "speed": 1.2}
            },
            "temporal": {
                "start_hour": 9,
                "picking_time_seconds": 60
            },
            "warehouse": {
                "width": 11,
                "height": 10,
                "entry_point": [6, 10]
            }
        }

def save_default_params(params):
    """Sauvegarde les paramètres par défaut dans le fichier JSON"""
    with open(DEFAULT_PARAMS_FILE, 'w') as f:
        json.dump(params, f, indent=2)

# === INITIALISATION DES PARAMÈTRES ===
if 'params' not in st.session_state:
    default_params = load_default_params()
    st.session_state['params'] = {
        # OR-Tools Solver
        'random_seed': default_params['solver']['random_seed'],
        'num_search_workers': default_params['solver']['num_search_workers'],
        'max_time_seconds': default_params['solver']['max_time_seconds'],
        
        # Gestion collisions
        'max_iterations': default_params['collision']['max_iterations'],
        'depot_time_minutes': default_params['collision']['depot_time_minutes'],
        
        # Coûts horaires (€/h)
        'cost_robot': default_params['costs']['robot_per_hour'],
        'cost_human': default_params['costs']['human_per_hour'],
        'cost_cart': default_params['costs']['cart_per_hour'],
        
        # Capacités & Vitesses (depuis agents.json)
        'capacity_robot': default_params['agents']['robot']['capacity_weight'],
        'capacity_robot_volume': default_params['agents']['robot']['capacity_volume'],
        'speed_robot': default_params['agents']['robot']['speed'],
        
        'capacity_human': default_params['agents']['human']['capacity_weight'],
        'capacity_human_volume': default_params['agents']['human']['capacity_volume'],
        'speed_human': default_params['agents']['human']['speed'],
        
        'capacity_cart': default_params['agents']['cart']['capacity_weight'],
        'capacity_cart_volume': default_params['agents']['cart']['capacity_volume'],
        'speed_cart': default_params['agents']['cart']['speed'],
        
        # Temporel
        'start_hour': default_params['temporal']['start_hour'],
        'picking_time_sec': default_params['temporal']['picking_time_seconds'],
        
        # Entrepôt
        'warehouse_width': default_params['warehouse']['width'],
        'warehouse_height': default_params['warehouse']['height'],
    }

# Stocker aussi les paramètres par défaut d'origine
if 'default_params_original' not in st.session_state:
    st.session_state['default_params_original'] = load_default_params()

# Configuration de la page
st.set_page_config(
    page_title="OPTIPICK - Optimisation d'Entrepôt",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre principal
st.title("🏭 OPTIPICK - Optimisation de Tournées d'Entrepôt")

# === SIDEBAR : CONFIGURATION ===
st.sidebar.header("⚙️ Configuration")

# Nombre de commandes
num_orders = st.sidebar.number_input(
    "Nombre de commandes à traiter",
    min_value=1,
    max_value=40,
    value=10,
    step=1,
    help="Sélectionnez le nombre de commandes à optimiser (1-40)"
)

# Bouton de lancement
if st.sidebar.button("🚀 LANCER L'OPTIMISATION", type="primary"):
    with st.spinner(f"⏳ Optimisation de {num_orders} commandes en cours..."):
        try:
            # Lancer l'optimisation avec les paramètres configurés
            result = run_optimization(
                num_orders,
                max_iterations=st.session_state['params']['max_iterations']
            )
            
            if result['status'] == 'success':
                st.session_state['result'] = result
                st.session_state['optimization_done'] = True
                st.sidebar.success(f"✓ Optimisation réussie !")
            else:
                st.sidebar.error(f"❌ Erreur : {result.get('message')}")
        except Exception as e:
            st.sidebar.error(f"❌ Erreur : {str(e)}")
else:
    st.sidebar.info("👆 Cliquez pour lancer l'optimisation")

st.sidebar.divider()

# Informations système
st.sidebar.subheader("ℹ️ Système")
st.sidebar.caption("Stratégie : MIN_TIME")
st.sidebar.caption("A* Pathfinding : ✓ Actif")
st.sidebar.caption(f"Max iterations : {st.session_state['params']['max_iterations']}")
st.sidebar.caption("Version : 1.0.0")

# === ONGLETS PRINCIPAUX ===
tab1, tab2, tab3 = st.tabs(["📊 STATISTIQUES", "🗺️ VISUALISATION", "⚙️ PARAMÈTRES"])

# === ONGLET 1 : STATISTIQUES ===
with tab1:
    st.header("📊 Statistiques de l'Optimisation")
    
    if 'optimization_done' not in st.session_state or 'result' not in st.session_state:
        st.info("👈 Lancez une optimisation depuis la barre latérale pour voir les statistiques")
    else:
        result = st.session_state['result']
        
        # === RÉSUMÉ GLOBAL ===
        st.subheader("🎯 Résumé Global")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Commandes", result['num_orders'])
        
        with col2:
            st.metric("Produits", result['total_products'])
        
        with col3:
            st.metric("Agents", result['agents_used'])
        
        with col4:
            st.metric("Temps global", result['temps_global_str'])
        
        st.divider()
        
        # === ANALYSE DES COÛTS ===
        st.subheader("💰 Analyse des Coûts")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Coût total", f"{result['total_cost']:.2f}€")
        
        with col2:
            st.metric("Coût/commande", f"{result['cost_per_order']:.2f}€")
        
        with col3:
            st.metric("Coût/agent", f"{result['cost_per_agent']:.2f}€")
        
        with col4:
            st.metric("Voyages totaux", result['total_voyages'])
        
        st.divider()
        
        # === DISTRIBUTION DES AGENTS ===
        st.subheader("👥 Distribution des Agents")
        
        import pandas as pd
        
        agent_data = []
        for stat in result['agent_stats']:
            agent_data.append({
                'Agent': stat['id'],
                'Type': stat['type'].upper(),
                'Produits': stat['nb_produits'],
                'Voyages': stat['nb_voyages'],
                'Début': stat['debut'],
                'Fin': stat['fin'],
                'Durée (min)': stat['duree_min'],
                'Coût (€)': f"{stat['cout']:.2f}",
                'Délai (min)': stat['delay']
            })
        
        df = pd.DataFrame(agent_data)
        
        # Afficher avec style
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Goulot d'étranglement
        if result['agent_stats']:
            bottleneck = result['agent_stats'][0]
            st.warning(
                f"Dernier agent terminant sa tournée : {bottleneck['id']} avec {bottleneck['nb_produits']} produits "
                f"en {bottleneck['nb_voyages']} voyages → Termine à {bottleneck['fin']} "
                f"(durée: {bottleneck['duree_min']} min)"
            )
        
        st.divider()
        
        # === COLLISIONS ===
        st.subheader("🚨 Collisions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if result['total_collisions'] == 0:
                st.success("✅ **Aucune collision !** Toutes les collisions ont été résolues.")
            elif result['total_collisions'] <= 3:
                st.info(f"ℹ️ **{result['total_collisions']} collisions résiduelles** (< 1% du temps)")
                st.caption("Ces collisions mineures sont acceptables et ne bloquent pas le système.")
            elif result['total_collisions'] <= 10:
                st.warning(f"⚠️ **{result['total_collisions']} collisions restantes** après résolution")
                st.caption(f"⚠️ Le système n'a pas pu toutes les résoudre. Les agents se croiseront {result['total_collisions']} fois.")
            else:
                st.error(f"❌ **{result['total_collisions']} collisions non résolues** (problème critique)")
                st.caption("❌ Trop de collisions ! Considérez : réduire les commandes, augmenter les délais, ou modifier la stratégie.")
        
        with col2:
            total_delay = sum(stat['delay'] for stat in result['agent_stats'])
            st.metric("Délais appliqués", f"{total_delay} min", help="Temps total de décalage appliqué aux agents pour éviter les collisions")
            
            # Nombre d'itérations utilisées
            if result['total_collisions'] > 0:
                st.caption(f"⚙️ {st.session_state['params']['max_iterations']} itérations utilisées")
                st.caption("💡 Si collisions persistent, augmenter max_iterations dans l'onglet PARAMÈTRES.")

# === ONGLET 2 : VISUALISATION ===
with tab2:
    st.header("🗺️ Visualisation de l'Entrepôt")
    
    if 'optimization_done' not in st.session_state or 'result' not in st.session_state:
        st.info("👈 Lancez une optimisation depuis la barre latérale pour voir la visualisation")
    else:
        result = st.session_state['result']
        
        # === CONTRÔLES ===
        st.subheader("🎛️ Contrôles")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Sélection agent
            trajectories = result['collision_result']['trajectories']
            agent_list = ['Tous les agents'] + list(trajectories.keys())
            selected_agent = st.selectbox(
                "Sélectionner un agent",
                agent_list,
                help="Choisir un agent spécifique ou tous les agents"
            )
        
        with col2:
            show_grid = st.checkbox("Afficher la grille", value=True)
        
        with col3:
            show_legend = st.checkbox("Afficher la légende", value=True)
        
        st.divider()
        
        # === CARTE ===
        st.subheader("🗺️ Carte de l'Entrepôt")
        
        from visualize_warehouse import create_warehouse_map, add_agent_trajectory, add_warehouse_legend
        import matplotlib.pyplot as plt
        
        # Créer la carte
        fig, ax = create_warehouse_map(result['warehouse'], show_grid=show_grid)
        
        # Couleurs des agents
        agent_colors = {
            'robot': '#FF4444',  # Rouge
            'human': '#4444FF',  # Bleu
            'cart': '#FF8800'    # Orange
        }
        
        # Dessiner les trajectoires
        trajectories = result['collision_result']['trajectories']
        depot_positions_all = result['collision_result']['depot_positions']
        agents_dict = {a['id']: a for a in result['agents']}
        
        if selected_agent == 'Tous les agents':
            # Afficher tous les agents
            for agent_id, trajectory in trajectories.items():
                agent = agents_dict[agent_id]
                color = agent_colors.get(agent['type'], '#666666')
                depot_pos = depot_positions_all.get(agent_id, [])
                add_agent_trajectory(ax, trajectory, agent_id, agent['type'], color, alpha=0.5, depot_positions=depot_pos)
        else:
            # Afficher un seul agent
            if selected_agent in trajectories:
                agent = agents_dict[selected_agent]
                color = agent_colors.get(agent['type'], '#666666')
                depot_pos = depot_positions_all.get(selected_agent, [])
                add_agent_trajectory(ax, trajectories[selected_agent], selected_agent, agent['type'], color, alpha=0.8, depot_positions=depot_pos)
        
        # Ajouter la légende si demandée
        if show_legend:
            add_warehouse_legend(ax)
        
        # Afficher la figure
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        
        # === LÉGENDE DES MARQUEURS ===
        st.divider()
        
        st.subheader("📋 Légende des Marqueurs")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("● **Cercle** : Point de départ (Entry)")
        
        with col2:
            st.markdown("◆ **Losange** : Dépôt effectué")
        
        with col3:
            st.markdown("★ **Étoile** : Retour final (Entry)")
        
        st.info("💡 **Règles** : Chaque agent a sa propre case de dépôt unique. Après le dernier article, l'agent dépose puis retourne à l'entry point.")
        
        st.divider()
        
        # === STATISTIQUES DE TRAJECTOIRE ===
        if selected_agent != 'Tous les agents' and selected_agent in trajectories:
            st.subheader(f"📈 Statistiques de {selected_agent}")
            
            # Trouver les stats de l'agent
            agent_stat = next((s for s in result['agent_stats'] if s['id'] == selected_agent), None)
            
            if agent_stat:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Temps de trajet", f"{len(trajectories[selected_agent])} min")
                
                with col2:
                    st.metric("Produits ramassés", agent_stat['nb_produits'])
                
                with col3:
                    st.metric("Voyages effectués", agent_stat['nb_voyages'])
                
                with col4:
                    st.metric("Coût", f"{agent_stat['cout']:.2f}€")

# === ONGLET 3 : PARAMÈTRES ===
with tab3:
    st.header("⚙️ Paramètres du Système")
    
    st.info("💡 **Attention** : Les modifications prennent effet lors de la prochaine optimisation.")
    
    # === SECTION 1 : OPTIMISATION OR-TOOLS ===
    st.subheader("🔧 Paramètres du Solver OR-Tools")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        random_seed = st.number_input(
            "Random Seed",
            min_value=0,
            max_value=99999,
            value=st.session_state['params']['random_seed'],
            step=1,
            help="Graine aléatoire pour résultats reproductibles"
        )
        st.session_state['params']['random_seed'] = random_seed
    
    with col2:
        num_threads = st.number_input(
            "Nombre de threads",
            min_value=1,
            max_value=16,
            value=st.session_state['params']['num_search_workers'],
            step=1,
            help="Nombre de threads parallèles pour le solver"
        )
        st.session_state['params']['num_search_workers'] = num_threads
    
    with col3:
        max_time_seconds = st.number_input(
            "Temps max résolution (sec)",
            min_value=10,
            max_value=600,
            value=st.session_state['params']['max_time_seconds'],
            step=10,
            help="Temps maximum alloué au solver"
        )
        st.session_state['params']['max_time_seconds'] = max_time_seconds
    
    st.caption("⚙️ Plus de threads = plus rapide. Temps élevé = meilleure solution.")
    
    st.divider()
    
    # === SECTION 2 : GESTION DES COLLISIONS ===
    st.subheader("🚨 Gestion des Collisions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_iterations = st.number_input(
            "Nombre max d'itérations",
            min_value=10,
            max_value=500,
            value=st.session_state['params']['max_iterations'],
            step=10,
            help="Nombre max de tentatives pour résoudre les collisions"
        )
        st.session_state['params']['max_iterations'] = max_iterations
    
    with col2:
        depot_time = st.number_input(
            "Temps au dépôt (min)",
            min_value=1,
            max_value=10,
            value=st.session_state['params']['depot_time_minutes'],
            step=1,
            help="Temps passé au dépôt pour déposer les produits"
        )
        st.session_state['params']['depot_time_minutes'] = depot_time
    
    st.caption("🚨 250 itérations recommandées. Plus d'itérations = plus de chances de résoudre toutes les collisions.")
    
    st.divider()
    
    # === SECTION 3 : COÛTS HORAIRES ===
    st.subheader("💰 Coûts Horaires des Agents")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cost_robot = st.number_input(
            "Coût Robot (€/h)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state['params']['cost_robot'],
            step=0.5
        )
        st.session_state['params']['cost_robot'] = cost_robot
    
    with col2:
        cost_human = st.number_input(
            "Coût Humain (€/h)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state['params']['cost_human'],
            step=0.5
        )
        st.session_state['params']['cost_human'] = cost_human
    
    with col3:
        cost_cart = st.number_input(
            "Coût Chariot (€/h)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state['params']['cost_cart'],
            step=0.5
        )
        st.session_state['params']['cost_cart'] = cost_cart
    
    st.caption("💰 Valeurs actuelles extraites de run_optimization.py")
    
    st.divider()
    
    # === SECTION 4 : VITESSES ET CAPACITÉS ===
    st.subheader("🏃 Vitesses et Capacités des Agents")
    
    st.write("**Robots**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state['params']['speed_robot'] = st.number_input("Vitesse (m/s)", min_value=0.1, max_value=5.0, value=st.session_state['params']['speed_robot'], step=0.1, key='speed_robot')
    with col2:
        st.session_state['params']['capacity_robot'] = st.number_input("Capacité poids (kg)", min_value=1, max_value=100, value=st.session_state['params']['capacity_robot'], step=1, key='cap_robot')
    with col3:
        st.session_state['params']['capacity_robot_volume'] = st.number_input("Capacité volume (dm³)", min_value=1, max_value=200, value=st.session_state['params']['capacity_robot_volume'], step=1, key='vol_robot')
    
    st.write("**Humains**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state['params']['speed_human'] = st.number_input("Vitesse (m/s)", min_value=0.1, max_value=5.0, value=st.session_state['params']['speed_human'], step=0.1, key='speed_human')
    with col2:
        st.session_state['params']['capacity_human'] = st.number_input("Capacité poids (kg)", min_value=1, max_value=100, value=st.session_state['params']['capacity_human'], step=1, key='cap_human')
    with col3:
        st.session_state['params']['capacity_human_volume'] = st.number_input("Capacité volume (dm³)", min_value=1, max_value=200, value=st.session_state['params']['capacity_human_volume'], step=1, key='vol_human')
    
    st.write("**Chariots**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state['params']['speed_cart'] = st.number_input("Vitesse (m/s)", min_value=0.1, max_value=5.0, value=st.session_state['params']['speed_cart'], step=0.1, key='speed_cart')
    with col2:
        st.session_state['params']['capacity_cart'] = st.number_input("Capacité poids (kg)", min_value=1, max_value=200, value=st.session_state['params']['capacity_cart'], step=5, key='cap_cart')
    with col3:
        st.session_state['params']['capacity_cart_volume'] = st.number_input("Capacité volume (dm³)", min_value=1, max_value=200, value=st.session_state['params']['capacity_cart_volume'], step=5, key='vol_cart')
    
    st.caption("📊 Valeurs actuelles extraites de agents.json")
    
    st.divider()
    
    # === SECTION 5 : TEMPOREL ===
    st.subheader("⏰ Paramètres Temporels")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_hour = st.number_input(
            "Heure de début (h)",
            min_value=0,
            max_value=23,
            value=st.session_state['params']['start_hour'],
            step=1
        )
        st.session_state['params']['start_hour'] = start_hour
    
    with col2:
        picking_time = st.number_input(
            "Temps de picking (sec)",
            min_value=5,
            max_value=300,
            value=st.session_state['params']['picking_time_sec'],
            step=5
        )
        st.session_state['params']['picking_time_sec'] = picking_time
    
    st.divider()
    
    # === SECTION 6 : ENTREPÔT ===
    st.subheader("📏 Dimensions de l'Entrepôt")
    
    col1, col2 = st.columns(2)
    
    with col1:
        warehouse_width = st.number_input(
            "Largeur (cases)",
            min_value=5,
            max_value=50,
            value=st.session_state['params']['warehouse_width'],
            step=1
        )
        st.session_state['params']['warehouse_width'] = warehouse_width
    
    with col2:
        warehouse_height = st.number_input(
            "Hauteur (cases)",
            min_value=5,
            max_value=50,
            value=st.session_state['params']['warehouse_height'],
            step=1
        )
        st.session_state['params']['warehouse_height'] = warehouse_height
    
    st.caption("📏 Valeurs actuelles de warehouse.json (11×10)")
    
    st.divider()
    
    # === BOUTONS D'ACTION ===
    st.subheader("💾 Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Réinitialiser aux valeurs par défaut", type="secondary"):
            st.session_state['params'] = {
                'random_seed': st.session_state['default_params_original']['solver']['random_seed'],
                'num_search_workers': st.session_state['default_params_original']['solver']['num_search_workers'],
                'max_time_seconds': st.session_state['default_params_original']['solver']['max_time_seconds'],
                'max_iterations': st.session_state['default_params_original']['collision']['max_iterations'],
                'depot_time_minutes': st.session_state['default_params_original']['collision']['depot_time_minutes'],
                'cost_robot': st.session_state['default_params_original']['costs']['robot_per_hour'],
                'cost_human': st.session_state['default_params_original']['costs']['human_per_hour'],
                'cost_cart': st.session_state['default_params_original']['costs']['cart_per_hour'],
                'capacity_robot': st.session_state['default_params_original']['agents']['robot']['capacity_weight'],
                'capacity_robot_volume': st.session_state['default_params_original']['agents']['robot']['capacity_volume'],
                'speed_robot': st.session_state['default_params_original']['agents']['robot']['speed'],
                'capacity_human': st.session_state['default_params_original']['agents']['human']['capacity_weight'],
                'capacity_human_volume': st.session_state['default_params_original']['agents']['human']['capacity_volume'],
                'speed_human': st.session_state['default_params_original']['agents']['human']['speed'],
                'capacity_cart': st.session_state['default_params_original']['agents']['cart']['capacity_weight'],
                'capacity_cart_volume': st.session_state['default_params_original']['agents']['cart']['capacity_volume'],
                'speed_cart': st.session_state['default_params_original']['agents']['cart']['speed'],
                'start_hour': st.session_state['default_params_original']['temporal']['start_hour'],
                'picking_time_sec': st.session_state['default_params_original']['temporal']['picking_time_seconds'],
                'warehouse_width': st.session_state['default_params_original']['warehouse']['width'],
                'warehouse_height': st.session_state['default_params_original']['warehouse']['height'],
            }
            st.success("✓ Paramètres réinitialisés aux valeurs par défaut d'origine !")
            st.rerun()
    
    with col2:
        if st.button("💾 Sauvegarder comme nouveaux défauts", type="primary"):
            # Construire le nouveau fichier de paramètres par défaut
            new_defaults = {
                "_comment": "Paramètres par défaut OPTIPICK - Mis à jour",
                "_version": "1.0",
                "_last_updated": "2026-02-20",
                "solver": {
                    "random_seed": st.session_state['params']['random_seed'],
                    "num_search_workers": st.session_state['params']['num_search_workers'],
                    "max_time_seconds": st.session_state['params']['max_time_seconds']
                },
                "collision": {
                    "max_iterations": st.session_state['params']['max_iterations'],
                    "depot_time_minutes": st.session_state['params']['depot_time_minutes']
                },
                "costs": {
                    "robot_per_hour": st.session_state['params']['cost_robot'],
                    "human_per_hour": st.session_state['params']['cost_human'],
                    "cart_per_hour": st.session_state['params']['cost_cart']
                },
                "agents": {
                    "robot": {
                        "capacity_weight": st.session_state['params']['capacity_robot'],
                        "capacity_volume": st.session_state['params']['capacity_robot_volume'],
                        "speed": st.session_state['params']['speed_robot']
                    },
                    "human": {
                        "capacity_weight": st.session_state['params']['capacity_human'],
                        "capacity_volume": st.session_state['params']['capacity_human_volume'],
                        "speed": st.session_state['params']['speed_human']
                    },
                    "cart": {
                        "capacity_weight": st.session_state['params']['capacity_cart'],
                        "capacity_volume": st.session_state['params']['capacity_cart_volume'],
                        "speed": st.session_state['params']['speed_cart']
                    }
                },
                "temporal": {
                    "start_hour": st.session_state['params']['start_hour'],
                    "picking_time_seconds": st.session_state['params']['picking_time_sec']
                },
                "warehouse": {
                    "width": st.session_state['params']['warehouse_width'],
                    "height": st.session_state['params']['warehouse_height'],
                    "entry_point": [6, 10]
                }
            }
            save_default_params(new_defaults)
            st.session_state['default_params_original'] = new_defaults
            st.success("✓ Les paramètres actuels sont maintenant les nouveaux paramètres par défaut !")
    
    with col3:
        params_json = json.dumps(st.session_state['params'], indent=2)
        st.download_button(
            label="📥 Exporter (JSON)",
            data=params_json,
            file_name="optipick_params.json",
            mime="application/json"
        )
    
    # Afficher résumé des modifications
    st.divider()
    st.info("💡 **Cliquez sur 'Sauvegarder comme nouveaux défauts' pour que vos modifications deviennent les paramètres par défaut au prochain lancement.**")

# === FOOTER ===
st.divider()
st.caption("OPTIPICK v1.0 - Optimisation de tournées avec OR-Tools CP-SAT | Paramètres extraits des fichiers sources")
