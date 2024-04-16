from scipy.optimize import linprog
import num2words

# Coefficients of the objective function (isk per unit) (negative because linprog does minimization) goes Industrial|Covert|Bastion|Tractor
c = [-8180000, -11350000, -9997000, -2600000]

# Coefficients of the inequality constraints (material limits) This is where you place the material needs. Remember: Industrial|Covert|Bastion|Tractor
A = [
    [20245, 12543, 350001, 25001],  # Tritanium
    [12915, 7542, 75000, 11000],    # Pyerite
    [2301, 1954, 30000, 9000],      # Mexallon
    [1098, 2125, 5001, 2501],       # Isogen
    [488, 891, 1000, 351],          # Nocxium
    [431, 1970, 400, 148],          # Zydrine
    [864, 1066, 200, 80]            # Megacyte
]
b = [17000000, 10500000, 319133, 800133, 188816, 129817, 109929]  # Material availability. Where you place the mats you have.

# Nocxium price (Since this is the only mineral I cant source)
NOXIUM_PRICE = 1114  # Replace with the actual Nocxium price

# Bounds for each variable, assuming non-negative integers
x_bounds = [(0, None), (0, None), (0, None), (0, None)]

# Solve the linear programming problem
result = linprog(c, A_ub=A, b_ub=b, bounds=x_bounds, method='highs')

if result.success:
    units_optimal = result.x.astype(int)
    profit_max = -result.fun
    print(f"Optimal number of units: {units_optimal}")
    

    # Calculate total required materials
    required_materials = {}
    for i, material in enumerate(['Tritanium', 'Pyerite', 'Mexallon', 'Isogen', 'Nocxium', 'Zydrine', 'Megacyte']):
        required_materials[material] = int(A[i][0] * units_optimal[0] + A[i][1] * units_optimal[1] + A[i][2] * units_optimal[2] + A[i][3] * units_optimal[3])

    # Subtract the cost of Nocxium from the maximum profit
    profit_max -= required_materials['Nocxium'] * NOXIUM_PRICE
    
    # Format the maximum profit to 2 decimal points and provide the word version
    profit_max_formatted = "{:,.2f}".format(profit_max)
    profit_max_words = num2words.num2words(int(profit_max), lang='en')
    print(f"Maximum profit: {profit_max_formatted} ISK ({profit_max_words.capitalize()} ISK)")
    print("Required materials for optimal number of units:")
    for material, amount in required_materials.items():
        print(f"{material}: {amount}")

    # Print the modules produced in the order: Industrial|Covert|Bastion|Tractor
    print("\nModules produced:")
    print(f"Industrial Cyno Field Generators: {int(units_optimal[0])}")
    print(f"Covert Cyno Field Generators: {int(units_optimal[1])}")
    print(f"Bastion Modules: {int(units_optimal[2])}")
    print(f"Small Tractor Beams: {int(units_optimal[3])}")
else:
    print("Optimization failed.")
    print(result.message)