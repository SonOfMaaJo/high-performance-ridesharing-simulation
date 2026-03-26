import pandas as pd
import numpy as np
import random

class DemandManager:
    def __init__(self, od_matrix_path, network_manager):
        self.od_matrix_path = od_matrix_path
        self.nm = network_manager
        self.df_od = None
        self.probabilities = []
        self.pairs = []

    def load_matrix(self):
        """Loads the OD matrix from a CSV (Support multiple formats)."""
        print(f"Loading OD matrix: {self.od_matrix_path}...")
        self.df_od = pd.read_csv(self.od_matrix_path)
        
        # Mapping variations to our internal standard (from_zone, to_zone, weight)
        mapping = {
            'O_ID': 'from_zone', 'o_zone_id': 'from_zone',
            'D_ID': 'to_zone', 'd_zone_id': 'to_zone',
            'OD_Number': 'weight', 'volume': 'weight'
        }
        
        # Apply renaming for any column found in our mapping
        self.df_od = self.df_od.rename(columns={k: v for k, v in mapping.items() if k in self.df_od.columns})
        
        # ENSURE EVERYTHING IS STRINGS FOR COMPARISON
        self.df_od['from_zone'] = self.df_od['from_zone'].astype(str)
        self.df_od['to_zone'] = self.df_od['to_zone'].astype(str)
        
        # Final check if we have the 3 required columns
        required = {'from_zone', 'to_zone', 'weight'}
        missing = required - set(self.df_od.columns)
        if missing:
            raise ValueError(f"Missing required columns in OD file: {missing}. Found: {self.df_od.columns.tolist()}")

        # Filter out zero weights to avoid selection errors
        self.df_od = self.df_od[self.df_od['weight'] > 0]
        
        total_flow = self.df_od['weight'].sum()
        self.df_od['prob'] = self.df_od['weight'] / total_flow
        
        self.pairs = list(zip(self.df_od['from_zone'], self.df_od['to_zone']))
        self.probabilities = self.df_od['prob'].tolist()
        return self.df_od

    def sample_trips(self, n):
        """Generates n trips (origin, destination) based on the OD matrix."""
        if not self.pairs:
            print("Error: OD matrix not loaded or empty.")
            return []

        # Choose n pairs of zones based on weights
        sampled_indices = np.random.choice(len(self.pairs), size=n, p=self.probabilities)
        
        trips = []
        # Cache nodes by zone for better performance
        zone_cache = {}

        for idx in sampled_indices:
            z_from, z_to = self.pairs[idx]
            
            if z_from not in zone_cache:
                zone_cache[z_from] = self.nm.get_nodes_in_zone(z_from)
            if z_to not in zone_cache:
                zone_cache[z_to] = self.nm.get_nodes_in_zone(z_to)
            
            nodes_from = zone_cache[z_from]
            nodes_to = zone_cache[z_to]
            
            # If a zone is empty in the graph, pick a random node elsewhere
            if not nodes_from:
                nodes_from = list(self.nm.graph.nodes)
            if not nodes_to:
                nodes_to = list(self.nm.graph.nodes)
                
            origin = random.choice(nodes_from)
            destination = random.choice(nodes_to)
            trips.append((origin, destination))
            
        return trips
