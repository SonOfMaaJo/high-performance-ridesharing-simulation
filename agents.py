import numpy as np

# Paramètres du modèle (Section 3 & 4 du PDF)
ALPHA_C = 0.5   # Coût unitaire transport motorisé (€/km -> converti en €/m)
ALPHA_M = 1.5   # Coût unitaire marche (plus élevé pour l'effort)
BETA = 0.01     # SDC : Pénalité avance (€/s)
GAMMA = 0.05    # SDC : Pénalité retard (€/s) -> GAMMA > BETA

def calculate_sdc(t_arrival, t_star):
    """Calcul du Schedule Delay Cost (Section 3.3 du PDF)."""
    delay = t_arrival - t_star
    if delay > 0:
        return GAMMA * delay # Retard
    else:
        return BETA * abs(delay) # Avance

class BaseAgent:
    __slots__ = ['id', 'origin', 'destination', 'profile']
    def __init__(self, id, origin, destination, profile=0):
        self.id = id
        self.origin = origin
        self.destination = destination
        self.profile = profile # Used for social compatibility

class Passenger(BaseAgent):
    __slots__ = ['t_h', 't_star', 'status']
    def __init__(self, id, origin, destination, t_h, t_star, profile=0):
        super().__init__(id, origin, destination, profile)
        self.t_h = t_h         # Real departure time (s)
        self.t_star = t_star   # Desired arrival time (s)
        self.status = "waiting" # waiting, riding, arrived

    def get_walking_cost(self, dist_m, current_time):
        """Walking cost C^M (Section 4.2)."""
        speed_walk = 1.39 # m/s
        travel_time = dist_m / speed_walk
        t_arrival = current_time + travel_time
        return (ALPHA_M * (dist_m/1000.0)) + calculate_sdc(t_arrival, self.t_star)

class Driver(BaseAgent):
    __slots__ = ['capacity', 'fixed_path', 'occupants', 'departure_time']
    def __init__(self, id, origin, destination, capacity=3, profile=0):
        super().__init__(id, origin, destination, profile)
        self.capacity = capacity
        self.fixed_path = [] 
        self.occupants = [] # List of passenger IDs on board
        self.departure_time = 0

    def set_fixed_path(self, graph):
        """Calcule le trajet fixe (plus court chemin)."""
        import networkx as nx
        self.fixed_path = nx.shortest_path(graph, self.origin, self.destination, weight='length')
        return self.fixed_path

    def is_compatible(self, passenger_profile):
        """Vérification binaire de compatibilité (Section 4.3)."""
        # Pour cet exemple : profils identiques = compatibles
        return self.profile == passenger_profile
