from scipy.optimize import linprog

# Coefficients of the objective function (isk per unit) (negative because linprog does minimization) goes industrial|covert|Bastion|tractor
c = [-10853211, -14438893, -12266199, -12025556]

# Coefficients of the inequality constraints (material limits)
A = [
    [20245, 12543, 350001, 25001],  # Tritanium
    [12915, 7542, 75000, 11000],    # Pyerite
    [2301, 1954, 30000, 9000],      # Mexallon
    [1098, 2125, 5001, 2501],       # Isogen
    [488, 891, 1000, 351],          # Nocxium
    [431, 1970, 400, 148],          # Zydrine
    [864, 1066, 200, 80]            # Megacyte
]
b = [17000000, 10500000, 319133, 800133, 188816, 129817, 109929]  # Material availability

# Bounds for each variable, assuming non-negative integers
x_bounds = [(0, None), (0, None), (0, None), (0, None)]

# Solve the linear programming problem
result = linprog(c, A_ub=A, b_ub=b, bounds=x_bounds, method='highs')

if result.success:
    units_optimal = result.x.astype(int)
    profit_max = -result.fun
    print(f"Optimal number of units: {units_optimal}")
    print(f"Maximum profit: {profit_max}")

    # Calculate required materials
    required_materials = {}
    for i, material in enumerate(['Tritanium', 'Pyerite', 'Mexallon', 'Isogen', 'Nocxium', 'Zydrine', 'Megacyte']):
        required_materials[material] = int(A[i][0] * units_optimal[0] + A[i][1] * units_optimal[1] + A[i][2] * units_optimal[2] + A[i][3] * units_optimal[3])

    print("Required materials for optimal number of units:")
    for material, amount in required_materials.items():
        print(f"{material}: {amount}")
else:
    print("Optimization failed.")
    print(result.message)