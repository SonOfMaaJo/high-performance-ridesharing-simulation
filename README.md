# Dynamic Ride-Sharing Simulation (Cergy-Pontoise & 20 US Cities)

This project provides a high-performance, city-scale dynamic ride-sharing simulation. It implements a stable matching algorithm (Gale-Shapley) to pair passengers and drivers based on real road networks and official Origin-Destination (OD) traffic flows.

## 🌟 Key Features

- **Multi-City Support**: Simulate ride-sharing in Cergy-Pontoise (France) or any of the 20 US cities from the 2024 Nature *Scientific Data* study (New York, Chicago, San Francisco, etc.).
- **Real-World Data**: Integration with OpenStreetMap (OSMNX) for road networks and Nature study Census Tracts for realistic traffic demand.
- **Dynamic Simulation**: Agents appear over time based on their departure schedules ($t_h$), with matching occurring at fixed intervals ($\Delta t$).
- **Stable Matching**: Implementation of the Gale-Shapley algorithm adapted for ride-sharing constraints (capacity, social compatibility, and timing).
- **Economic Modeling**: Includes Travel Cost and **Schedule Delay Cost (SDC)** to penalize early or late arrivals.

## 🚀 High-Performance Optimizations

To handle up to **1,000,000 agents** efficiently, the engine includes:

1.  **igraph Routing Engine**: Road networks are converted from NetworkX to `igraph` (C-based), providing a **10x-50x speedup** in shortest-path calculations.
2.  **Parallel Processing**: Heavy preference list computations are automatically distributed across all available CPU cores using Python's `multiprocessing`.
3.  **Memory Optimization**: Use of `__slots__` in Agent classes reduces RAM footprint by nearly **50%**, allowing massive simulations on standard hardware.
4.  **Spatial Indexing (KDTree)** : Uses `scipy.spatial.KDTree` for ultra-fast neighborhood searches, avoiding unnecessary Dijkstra calculations.
5.  **Top-K Dijkstra Filtering**: Only the top candidates identified geometrically are evaluated for real road distance, drastically reducing complexity.

## 🛠️ Installation

Ensure you have the required dependencies:

```bash
pip install osmnx python-igraph geopandas pandas numpy scipy tqdm networkx psutil
```

## 💻 Usage

Use the universal CLI `main.py` to launch any simulation.

### Basic Examples

**Run Cergy (Default):**
```bash
python3 main.py --passengers 1000 --drivers 200
```

**Run Chicago (USA) with official flows:**
```bash
python3 main.py --city "Chicago" --state "IL" --country "USA" --passengers 5000 --drivers 1000
```

**Run New York (USA) with custom time step:**
```bash
python3 main.py --city "New York" --state "NY" --country "USA" --passengers 10000 --step 600
```

### CLI Arguments
- `--city`: Name of the city.
- `--passengers`: Total number of passengers to simulate.
- `--drivers`: Total number of drivers.
- `--state`: State/Region code (required for USA).
- `--country`: Country name (default: France).
- `--step`: Time step in seconds (default: 300s).

## 📁 Project Structure

- `main.py`: Entry point for the CLI.
- `simulation_cergy.py`: Main simulation loop logic.
- `matching.py`: Gale-Shapley matching implementation with parallel support.
- `network_manager.py`: Graph management (OSM + igraph) and zone mapping.
- `demand_manager.py`: OD Matrix parsing and agent generation.
- `agents.py`: Data models for Passengers and Drivers (Memory-optimized).
- `data/`: Directory for graphs and OD matrices (Nature dataset subfolders).

## 📊 References
- Nature Scientific Data (2024): *"A unified dataset for the city-scale traffic assignment model in 20 U.S. cities"*.
- OpenStreetMap contributors.
