import time
import random
import os
from network_manager import NetworkManager
from agents import Passenger, Driver
from matching import StableMatching
from demand_manager import DemandManager
from tqdm import tqdm

def run_dynamic_simulation(city="Cergy", state=None, country="France", num_passengers=500, num_drivers=100, delta_t=300):
    nm = NetworkManager(city, state, country)
    G = nm.load_or_download_graph()
    
    # LOAD ZONES AND OD MATRIX
    nm.load_zones()
    nm.map_nodes_to_zones()
    
    # Locate OD Matrix (Support city-specific subfolders and Nature dataset structure)
    city_slug = city.lower().replace(" ", "_")
    
    # List of potential paths to search for the OD file
    potential_paths = [
        f"data/{city_slug}_od.csv",
        f"data/{city}_od.csv",
        "data/od_matrix.csv" # Default fallback
    ]
    
    # Add Nature dataset specific paths
    if os.path.exists("data"):
        for root, dirs, files in os.walk("data"):
            for file in files:
                if file.lower() == f"{city_slug}_od.csv" or file.lower() == f"{city}_od.csv":
                    potential_paths.insert(0, os.path.join(root, file))

    od_path = "data/od_matrix.csv" # Ultimate fallback
    for path in potential_paths:
        if os.path.exists(path):
            od_path = path
            break
            
    print(f"Using OD Matrix file: {od_path}")
    dm = DemandManager(od_path, nm)
    dm.load_matrix()
    
    # 1. Generate agents based on OD matrix
    print(f"Generating {num_passengers} passengers via OD matrix for {city}...")
    passenger_trips = dm.sample_trips(num_passengers)
    
    passengers = []
    for i in range(num_passengers):
        t_h = random.randint(0, 3600) # Departure between 0 and 1h
        t_star = t_h + 1800 + random.randint(0, 1800) # Desired arrival ~45min later
        profile = random.randint(0, 1) # 2 social profiles
        origin, destination = passenger_trips[i]
        passengers.append(Passenger(f"P{i}", origin, destination, t_h, t_star, profile))
        
    print(f"Generating {num_drivers} drivers via OD matrix...")
    driver_trips = dm.sample_trips(num_drivers)
    
    drivers = []
    for i in range(num_drivers):
        origin, destination = driver_trips[i]
        d = Driver(f"D{i}", origin, destination, profile=random.randint(0, 1))
        d.set_fixed_path(G)
        drivers.append(d)
    
    # 2. Time loop T
    start_sim_time = time.time()
    total_matches = 0
    active_drivers = {d.id: d for d in drivers}
    total_capacity = sum(d.capacity for d in drivers)
    
    print(f"Dynamic simulation for {num_passengers} passengers...")
    for t in tqdm(range(0, 7200, delta_t), desc="Time loop"): # 2-hour simulation
        # Identify passengers arriving at t
        p_active_at_t = [p for p in passengers if t <= p.t_h < t + delta_t]
        
        if not p_active_at_t:
            continue
            
        sm = StableMatching(p_active_at_t, active_drivers, G, t, nm)
        p_prefs, d_prefs = sm.build_preference_lists()
        matches = sm.solve(p_prefs, d_prefs)
        
        # Apply results
        step_matches = 0
        for d_id, p_ids in matches.items():
            active_drivers[d_id].occupants.extend(p_ids)
            step_matches += len(p_ids)
        
        total_matches += step_matches

    end_sim_time = time.time()
    
    # 3. Final Statistics
    print("\n" + "="*40)
    print(" FINAL SIMULATION STATISTICS")
    print("="*40)
    print(f"Total computation time : {end_sim_time - start_sim_time:.2f} seconds")
    print(f"Total passengers : {num_passengers}")
    print(f"Total drivers : {num_drivers}")
    print(f"Theoretical total capacity : {total_capacity} seats")
    print("-" * 40)
    print(f"Total matches : {total_matches}")
    print(f"Number of walking passengers : {num_passengers - total_matches}")
    print("-" * 40)
    matching_rate = (total_matches / num_passengers) * 100
    occupancy_rate = (total_matches / total_capacity) * 100
    print(f"Passenger Matching Rate : {matching_rate:.2f} %")
    print(f"Vehicle Occupancy Rate : {occupancy_rate:.2f} %")
    print("="*40 + "\n")

if __name__ == "__main__":
    run_dynamic_simulation(num_passengers=100, num_drivers=20)
