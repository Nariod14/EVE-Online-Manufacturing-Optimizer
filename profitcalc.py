import num2words
from pulp import PULP_CBC_CMD, LpMinimize, LpProblem, LpVariable, lpSum, value

# Coefficients of the objective function (ISK per unit) (negative because linprog does minimization)
# Order: Industrial|Covert|Bastion|Tractor|Defender Launcher|Large Asteroid Ore Compressor I|Medium Asteroid Ore Compressor I
c = [
    -7459000,  # Industrial Cynosural Field Generator
    -11930000, # Covert Cynosural Field Generator I
    -10620000, # Bastion Module I
    -3079000,  # Small Tractor Beam I
    -8220000,  # Defender Launcher I
    -23560000, # Large Asteroid Ore Compressor I
    -12920000  # Medium Asteroid Ore Compressor I
]


# Coefficients of the inequality constraints (material limits)
# Order of materials: Tritanium|Pyerite|Mexallon|Isogen|Nocxium|Zydrine|Megacyte
A = [
    [20044, 12418, 346521, 24752, 92426, 135143, 68314],  # Tritanium
    [12786, 7467, 74255, 10891, 28111, 135143, 68314],  # Pyerite
    [2278, 1935, 29702, 8911, 5763, 36039, 18217],  # Mexallon
    [1088, 2105, 4951, 2408, 3708, 18020, 9109],  # Isogen
    [483, 882, 991, 348, 1379, 902, 456],  # Nocxium
    [450, 1950, 396, 146, 482, 902, 456],  # Zydrine
    [902, 1055, 198, 79, 385, 902, 456],  # Megacyte
]
b = [
    150780360,  # Tritanium
    8244348,    # Pyerite
    7206966,    # Mexallon
    2513227,    # Isogen
    900101,     # Nocxium
    288883,     # Zydrine
    85913,      # Megacyte
]  # Material availability


# Nocxium price (since this is the only mineral you can't source)
NOXIUM_PRICE = 984  # Replace with the actual Nocxium price

# Bounds for each variable, assuming non-negative integers
x_bounds = [(0, None)] * 7  # Adjust for 7 variables

# Create the LP problem
prob = LpProblem("Modules Optimization", LpMinimize)

# Define the decision variables
x = [LpVariable(f"x{i}", 0, None, cat="Integer") for i in range(7)]

# Set the objective function
prob += lpSum(c[i] * x[i] for i in range(7))

# Add the inequality constraints
for i in range(7):
    prob += lpSum(A[i][j] * x[j] for j in range(7)) <= b[i]
# Additional constraints in order to not crash the market
prob += x[3] <= 450  # Limit Small Tractor Beam Is to 500
prob += x[4] <= 75  # Limit Defender Launcher I to 150
prob += x[5] <= 50  # Limit Large Asteroid Ore Compressor Is to 45
prob += x[6] <= 50  # Limit Medium Asteroid Ore Compressor I to 45

# Solve the problem
prob.solve(PULP_CBC_CMD(msg=False))

if prob.status == 1:
    units_optimal = [int(v.value()) for v in x]
    profit_max = -value(prob.objective)

    # Calculate total required materials for optimal units
    required_materials = {}
    for i, material in enumerate(
        ["Tritanium", "Pyerite", "Mexallon", "Isogen", "Nocxium", "Zydrine", "Megacyte"]
    ):
        required_materials[material] = sum(
            A[i][j] * units_optimal[j] for j in range(len(units_optimal))
        )

    # Subtract the cost of Nocxium from the maximum profit
    profit_max -= required_materials["Nocxium"] * NOXIUM_PRICE

    # Format the maximum profit to 2 decimal points and provide the word version
    profit_max_formatted = "{:,.2f}".format(profit_max)
    profit_max_words = num2words.num2words(int(profit_max), lang="en")

    ## Optimal Solution
    print(f"Optimal number of units: {units_optimal}")
    print(
        f"Maximum profit: {profit_max_formatted} ISK ({profit_max_words.capitalize()} ISK)"
    )

    ## Required Materials
    print("\nRequired materials for optimal number of units:")
    for material, amount in required_materials.items():
        print(f"{material}: {amount}")

    ## Modules Produced
    print("\nModules produced:")
    print(f"Industrial Cyno Field Generators: {int(units_optimal[0])}")
    print(f"Covert Cyno Field Generators: {int(units_optimal[1])}")
    print(f"Bastion Modules: {int(units_optimal[2])}")
    print(f"Small Tractor Beams: {int(units_optimal[3])}")
    print(f"Defender Launcher I: {int(units_optimal[4])}")
    print(f"Large Asteroid Ore Compressor I: {int(units_optimal[5])}")
    print(f"Medium Asteroid Ore Compressor I: {int(units_optimal[6])}")
else:
    print("Optimization failed.")
    print(prob.status)
