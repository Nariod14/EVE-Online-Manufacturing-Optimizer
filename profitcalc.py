import num2words
from pulp import LpProblem, LpMinimize, LpVariable, value, lpSum, PULP_CBC_CMD

# Coefficients of the objective function (ISK per unit) (negative because linprog does minimization)
# Order: Industrial|Covert|Bastion|Tractor|Defender Launcher
c = [-8294000, -12640000, -10540000, -2855000, -8494000]

# Coefficients of the inequality constraints (material limits)
# Order of materials: Tritanium|Pyerite|Mexallon|Isogen|Nocxium|Zydrine|Megacyte
A = [
    [19201, 11896, 331948, 23711, 88539],   # Tritanium
    [12248, 7153, 71132, 10433, 26929],  # Pyerite
    [2182, 1854, 28453, 8536, 5521],     # Mexallon
    [1042, 2016, 4743, 2307, 3552],      # Isogen
    [463, 845, 949, 333, 1321],         # Nocxium
    [431, 1868, 379, 140, 462],          # Zydrine
    [864, 1011, 190, 76, 369]            # Megacyte
]
b = [40938408, 11440607, 7050696, 1925413, 109086, 205630, 95486]  # Material availability

# Nocxium price (since this is the only mineral you can't source)
NOXIUM_PRICE = 1078  # Replace with the actual Nocxium price

# Bounds for each variable, assuming non-negative integers
x_bounds = [(0, None)] * 5  # Adjust for 5 variables (Industrial, Covert, Bastion, Tractor, Defender Launcher)

# Create the LP problem
prob = LpProblem("Modules Optimization", LpMinimize)

# Define the decision variables
x = [LpVariable(f"x{i}", 0, None, cat="Integer") for i in range(5)]

# Set the objective function
prob += lpSum(c[i] * x[i] for i in range(5))

# Add the inequality constraints
for i in range(7):
    prob += lpSum(A[i][j] * x[j] for j in range(5)) <= b[i]

# Solve the problem
prob.solve(PULP_CBC_CMD(msg=False))

if prob.status == 1:
    units_optimal = [int(v.value()) for v in x]
    profit_max = -value(prob.objective)
    
    # Calculate total required materials for optimal units
    required_materials = {}
    for i, material in enumerate(['Tritanium', 'Pyerite', 'Mexallon', 'Isogen', 'Nocxium', 'Zydrine', 'Megacyte']):
        required_materials[material] = sum(A[i][j] * units_optimal[j] for j in range(len(units_optimal)))

    # Subtract the cost of Nocxium from the maximum profit
    profit_max -= required_materials['Nocxium'] * NOXIUM_PRICE
    
    # Format the maximum profit to 2 decimal points and provide the word version
    profit_max_formatted = "{:,.2f}".format(profit_max)
    profit_max_words = num2words.num2words(int(profit_max), lang='en')
    
    ## Optimal Solution
    print(f"Optimal number of units: {units_optimal}")
    print(f"Maximum profit: {profit_max_formatted} ISK ({profit_max_words.capitalize()} ISK)")
    
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
else:
    print("Optimization failed.")
    print(prob.status)