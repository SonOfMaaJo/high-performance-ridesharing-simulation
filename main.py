import argparse
from simulation_cergy import run_dynamic_simulation

def main():
    parser = argparse.ArgumentParser(description="Ride-sharing Simulation CLI")
    
    # Core Arguments
    parser.add_argument("--city", type=str, default="Cergy", help="City name (e.g., 'San Francisco', 'Chicago')")
    parser.add_argument("--passengers", type=int, default=500, help="Number of passengers")
    parser.add_argument("--drivers", type=int, default=100, help="Number of drivers")
    
    # Localization Arguments
    parser.add_argument("--state", type=str, default=None, help="State/Region code (e.g., 'CA', 'IL', 'NY')")
    parser.add_argument("--country", type=str, default="France", help="Country name (e.g., 'USA', 'France')")
    
    # Simulation Parameters
    parser.add_argument("--step", type=int, default=300, help="Time step delta_t in seconds (default: 300s)")
    
    args = parser.parse_args()

    print(f"\n>>> LAUNCHING SIMULATION: {args.city} ({args.country})")
    print(f">>> CONFIG: {args.passengers} passengers, {args.drivers} drivers, step={args.step}s")
    print("-" * 50)

    try:
        run_dynamic_simulation(
            city=args.city,
            state=args.state,
            country=args.country,
            num_passengers=args.passengers,
            num_drivers=args.drivers,
            delta_t=args.step
        )
    except Exception as e:
        print(f"\n[!] ERROR during simulation: {e}")

if __name__ == "__main__":
    main()
