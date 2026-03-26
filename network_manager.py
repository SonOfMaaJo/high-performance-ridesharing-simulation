import osmnx as ox
import networkx as nx
import pickle
import os

class NetworkManager:
    def __init__(self, city="Cergy", state=None, country="France"):
        self.city = city
        self.state = state
        self.country = country
        
        # Build full place name
        if state:
            self.city_name = f"{city}, {state}, {country}"
        else:
            self.city_name = f"{city}, {country}"
            
        self.graph_path = f"data/{self.city_name.replace(', ', '_')}.graphml"
        self.graph = None
        self.igraph = None # igraph version for high-speed routing
        self.osm_to_igraph = {} # Mapping OSM node ID -> igraph index
        self.zones = None # GeoDataFrame of neighborhoods/Census Tracts
        self.node_to_zone = {} # Mapping node_id -> zone_name

    def load_or_download_graph(self):
        """Loads the graph and converts it to igraph for performance."""
        if os.path.exists(self.graph_path):
            print(f"Loading graph for {self.city_name} from {self.graph_path}...")
            self.graph = ox.load_graphml(self.graph_path)
        else:
            print(f"Downloading graph for {self.city_name} via OSMNX...")
            if not os.path.exists("data"):
                os.makedirs("data")
            self.graph = ox.graph_from_place(self.city_name, network_type="drive")
            self.graph = ox.project_graph(self.graph)
            self.graph = ox.truncate.largest_component(self.graph, strongly=True)
            ox.save_graphml(self.graph, self.graph_path)
        
        self._convert_to_igraph()
        return self.graph

    def _convert_to_igraph(self):
        """Converts the NetworkX graph to an igraph for much faster Dijkstra."""
        print("Converting graph to igraph format (High Speed)...")
        import igraph as ig
        
        # Map OSM nodes to 0-based indices for igraph
        self.osm_to_igraph = {node: i for i, node in enumerate(self.graph.nodes())}
        self.igraph_to_osm = {i: node for node, i in self.osm_to_igraph.items()}
        
        # Extract edges and weights (length)
        edges = []
        weights = []
        for u, v, data in self.graph.edges(data=True):
            edges.append((self.osm_to_igraph[u], self.osm_to_igraph[v]))
            weights.append(data.get('length', 1.0))
            
        # Create igraph
        self.igraph = ig.Graph(len(self.graph.nodes()), edges, directed=True)
        self.igraph.es['weight'] = weights
        print(f"igraph created with {self.igraph.vcount()} nodes and {self.igraph.ecount()} edges.")

    def get_shortest_path_length(self, source_node, target_node):
        """Calculates shortest distance using igraph (Fast)."""
        if self.igraph:
            u_idx = self.osm_to_igraph[source_node]
            v_idx = self.osm_to_igraph[target_node]
            # igraph returns a list of lists for shortest paths
            dist = self.igraph.distances(source=u_idx, target=v_idx, weights='weight')[0][0]
            return dist
        return nx.shortest_path_length(self.graph, source_node, target_node, weight="length")

    def load_zones(self):
        """Fetches neighborhood polygons (admin_level=10 for FR, or various tags for US) via OSMNX."""
        print(f"Fetching neighborhoods for {self.city_name}...")
        try:
            if self.country == "USA":
                # For USA, census tracts are sometimes under 'boundary=census' 
                # but often neighborhoods are simply 'place=neighborhood' or 'boundary=administrative'
                print("Searching for US zones (Census, Administrative or Neighborhoods)...")
                # Try multiple tags in sequence
                tags_to_try = [
                    {"boundary": "census"},
                    {"boundary": "administrative", "admin_level": "10"},
                    {"place": "neighborhood"}
                ]
                
                for tags in tags_to_try:
                    try:
                        self.zones = ox.features_from_place(self.city_name, tags=tags)
                        if not self.zones.empty:
                            print(f"Found {len(self.zones)} zones using {tags}")
                            break
                    except:
                        continue
                
                if self.zones is None or self.zones.empty:
                    print("Could not find specific US zones, falling back to city boundary.")
                    self.zones = ox.geocode_to_gdf(self.city_name)
            else:
                # For France/Others
                self.zones = ox.features_from_place(self.city_name, tags={"admin_level": "10"})
            
            # Keep only useful columns (name and geometry)
            possible_name_cols = ['name', 'census_name', 'neighborhood', 'display_name']
            name_col = next((c for c in possible_name_cols if c in self.zones.columns), None)
            
            if name_col:
                self.zones = self.zones[[name_col, 'geometry']].rename(columns={name_col: 'name'})
            else:
                # If no name column, create a dummy one
                self.zones['name'] = [f"Zone_{i}" for i in range(len(self.zones))]
                self.zones = self.zones[['name', 'geometry']]
            
            print(f"{len(self.zones)} neighborhoods/zones successfully loaded.")
        except Exception as e:
            print(f"Error while loading zones: {e}")
            self.zones = None
        return self.zones

    def map_nodes_to_zones(self):
        """Assigns each node to a neighborhood/tract. 
        Supports Nature dataset (via node.csv) and OSM zones."""
        if self.graph is None:
            print("Error: Graph not loaded.")
            return

        # 1. Check if Nature study node file exists for this city
        city_slug = self.city.replace(" ", "_")
        node_csv_path = None
        if os.path.exists("data"):
            for root, dirs, files in os.walk("data"):
                for file in files:
                    if file.lower() == f"{city_slug.lower()}_node.csv":
                        node_csv_path = os.path.join(root, file)
                        break

        if node_csv_path:
            print(f"Detected Nature study node file: {node_csv_path}")
            print("Mapping nodes using Nature study Census Tracts...")
            import pandas as pd
            from scipy.spatial import KDTree
            
            # Load study nodes
            df_nodes = pd.read_csv(node_csv_path)
            # Identify Tract nodes (Centroids used in OD matrix)
            # In Nature study, they are typically the ones with IDs >= 10,000,000
            tract_nodes = df_nodes[df_nodes['Node_ID'] >= 10000000].copy()
            if tract_nodes.empty:
                tract_nodes = df_nodes[df_nodes['Tract_Node'] == 1].copy()
            
            print(f"Identified {len(tract_nodes)} traffic zones (Centroids).")
            
            # KDTree of zone centroids
            tract_coords = tract_nodes[['Lon', 'Lat']].values
            tract_tree = KDTree(tract_coords)
            
            # Map every OSM node to its NEAREST traffic zone
            self.node_to_zone = {}
            for node_id, data in self.graph.nodes(data=True):
                osm_coord = [data['x'], data['y']]
                dist, idx = tract_tree.query(osm_coord)
                self.node_to_zone[node_id] = str(int(tract_nodes.iloc[idx]['Node_ID']))
            
            print(f"Successfully mapped {len(self.node_to_zone)} nodes to {len(tract_nodes)} zones.")
            return self.node_to_zone

        # 2. Fallback to spatial join with OSM zones (Polygons)
        if self.zones is None:
            print("No zones loaded (OSM or Study). Mapping will fail.")
            return

        print("Mapping nodes to OSM neighborhoods (Polygons)...")
        # Convert graph to GeoDataFrame of points
        gdf_nodes = ox.graph_to_gdfs(self.graph, nodes=True, edges=False)
        
        # FIX: Ensure CRS match before spatial join
        if gdf_nodes.crs != self.zones.crs:
            self.zones = self.zones.to_crs(gdf_nodes.crs)
            
        # Spatial join to find which node is within which polygon
        import geopandas as gpd
        nodes_with_zones = gpd.sjoin(gdf_nodes, self.zones, how="left", predicate="within")
        
        # Populate mapping dictionary
        self.node_to_zone = {}
        for node_id, row in nodes_with_zones.iterrows():
            zone_name = row['name'] if not str(row['name']) == 'nan' else "Unknown"
            self.node_to_zone[node_id] = str(zone_name)
        
        return self.node_to_zone

    def get_nodes_in_zone(self, zone_name):
        """Returns the list of nodes belonging to a specific zone."""
        return [node for node, zone in self.node_to_zone.items() if zone == zone_name]

    def get_random_nodes(self, n, unique=True):
        """Returns n random nodes from the graph."""
        import random
        nodes = list(self.graph.nodes)
        if unique:
            if n > len(nodes):
                raise ValueError(f"Requested {n} unique nodes but graph only contains {len(nodes)}.")
            return random.sample(nodes, n)
        else:
            return random.choices(nodes, k=n)

if __name__ == "__main__":
    # Test for Cergy
    nm = NetworkManager("Cergy", country="France")
    G = nm.load_or_download_graph()
    print(f"Cergy loaded: {len(G.nodes)} nodes.")
