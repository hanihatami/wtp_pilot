import numpy as np
import itertools

############################## Constants ##############################
HOURS = 24  # Simulation period
PRODUCTS = 30 # Number of products 30
CONTAINER_SIZES = [70, 100, 150, 400, 20, 90, 80, 60] * 10  # Possible container sizes 
HOURLY_SALES = [20, 40, 60, 80, 10]  # Hourly sales for each product
MAX_TOTAL_CONTAINER_SIZE = 2000  # Maximum allowed sum of container sizes
MAX_REFILLS_PER_TRIP = 5  # Maximum number of products that can be refilled in one trip
REFILL_FRACTION = 1  # Fraction of original size at which a container becomes a refill priority
############################## Simulation ################################
def simulate_operation(container_assignments, max_refills_per_trip, refill_fraction):
    '''
    Function to simulate the operation for a given set of container sizes
    '''
    containers = np.array(container_assignments) 
    original_capacities = containers.copy()  # Keep track of the original capacities
    trips = 0
    
    for hour in range(HOURS):
        # Decrease containers based on hourly sales
        containers -= HOURLY_SALES
        
        # Determine refill priorities
        empty_or_low = (containers <= 0) | (containers <= original_capacities * refill_fraction)
        # Generate a priority list: empty containers first, then low containers
        priority_indices = np.lexsort((empty_or_low, containers <= 0))
        
        # Track refills for this trip
        refills_this_trip = 0
        
        while np.any(containers <= 0):
            for i in priority_indices:
                if (containers[i] <= 0 or containers[i] <= original_capacities[i] * refill_fraction) and refills_this_trip < max_refills_per_trip:
                    containers[i] = original_capacities[i]  # Refill
                    refills_this_trip += 1
                    if refills_this_trip == max_refills_per_trip:
                        break  # Reached max refills for this trip
            
            if refills_this_trip > 0:
                trips += 1  # Count this trip
                refills_this_trip = 0  # Reset for next potential trip
            
            # If there are still containers that need refilling but we've hit our refill limit,
            # they'll be handled in the next iteration/trip.
            if np.any(containers <= 0):
                continue  # Check if another trip is needed immediately
                
    return trips

# search over all unique combinations of container sizes
min_trips = np.inf
optimal_assignments = []

# Generate all unique combinations of container sizes for the products without repetition
# and filter out combinations where the total size exceeds the maximum allowed sum.
valid_combinations = [
    combo for combo in itertools.combinations(CONTAINER_SIZES, PRODUCTS)
    if sum(combo) <= MAX_TOTAL_CONTAINER_SIZE
]

# Generate all unique combinations of container sizes for the products
for assignment in valid_combinations:
    trips = simulate_operation(list(assignment), MAX_REFILLS_PER_TRIP, REFILL_FRACTION)
    if trips < min_trips:
        min_trips = trips
        optimal_assignments = [assignment] # Start a new list with this better result
    elif trips == min_trips:
        optimal_assignments.append(assignment)  # Add to the list of optimal solutions

# From the optimal solutions, select the one with the greatest total container size
best_assignment = max(optimal_assignments, key=lambda x: sum(x))


# Results
print("Best container assignments:", list(best_assignment))
print("Minimum number of trips:", min_trips)
# CONTAINER_SIZES = [70, 100, 150, 40, 20, 90, 80, 60] 
# HOURLY_SALES = [20, 40, 60, 80, 10]