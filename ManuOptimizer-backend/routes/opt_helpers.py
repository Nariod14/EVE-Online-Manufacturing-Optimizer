import logging
from collections import defaultdict, deque
from models import Blueprint as BlueprintModel, Material



logger = logging.getLogger(__name__)


class ProductionOptimizer:
    def __init__(self, blueprints, materials, inventory):
        self.blueprints = {bp.name: bp for bp in blueprints}
        self.materials = {m.name: m for m in materials}
        self.inventory = inventory.copy()
        self.initial_inventory = inventory.copy()
        
        # Build dependency graph
        self.dependencies = self._build_dependency_graph()
        self.production_order = self._get_production_order()
        
    def _build_dependency_graph(self):
        """Build a graph of what each blueprint needs"""
        deps = {}
        for bp_name, bp in self.blueprints.items():
            deps[bp_name] = []
            materials = bp.get_normalized_materials()
            
            # Materials are structured as: {"Category": {"MaterialName": {"quantity": X}}}
            for category, category_materials in materials.items():
                if isinstance(category_materials, dict):
                    for material_name, material_data in category_materials.items():
                        # Check if this material has a blueprint (can be produced)
                        if material_name and material_name in self.blueprints:
                            deps[bp_name].append(material_name)
        return deps
    
    def _get_production_order(self):
        """Topological sort to determine production order"""
        # Kahn's algorithm for topological sorting
        in_degree = {bp: 0 for bp in self.blueprints}
        
        # Calculate in-degrees
        for bp_name in self.blueprints:
            for dep in self.dependencies[bp_name]:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Start with items that have no dependencies
        queue = deque([bp for bp, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Reduce in-degree for dependent items
            for bp_name in self.blueprints:
                if current in self.dependencies[bp_name]:
                    in_degree[bp_name] -= 1
                    if in_degree[bp_name] == 0:
                        queue.append(bp_name)
        
        return result
    
    def _calculate_profit_per_unit(self, blueprint_name):
        """Calculate profit per unit for a blueprint"""
        bp = self.blueprints[blueprint_name]
        
        # Calculate actual production cost based on current inventory/market
        production_cost = 0
        materials = bp.get_normalized_materials()
        
        # Materials are structured as: {"Category": {"MaterialName": {"quantity": X}}}
        for category, category_materials in materials.items():
            if isinstance(category_materials, dict):
                for material_name, material_data in category_materials.items():
                    material_qty = material_data.get('quantity', 1) if isinstance(material_data, dict) else 1
                    
                    if material_name in self.materials:
                        material_obj = self.materials[material_name]
                        
                        # If we can produce this material, calculate recursive cost
                        if material_name in self.blueprints:
                            recursive_cost = self._calculate_recursive_cost(material_name, material_qty)
                            production_cost += recursive_cost
                        else:
                            # Use market price
                            production_cost += material_qty * material_obj.sell_price
        
        # Profit per unit = sell price - production cost per unit
        profit_per_unit = bp.sell_price - (production_cost / bp.amt_per_run)
        return profit_per_unit
    
    def _calculate_recursive_cost(self, item_name, quantity_needed):
        """Calculate cost of producing an item recursively"""
        if item_name not in self.blueprints:
            # Base material, use market price
            if item_name in self.materials:
                return quantity_needed * self.materials[item_name].sell_price
            return 0
        
        bp = self.blueprints[item_name]
        
        # Calculate cost to produce one batch
        batch_cost = 0
        materials = bp.get_normalized_materials()
        
        # Materials are structured as: {"Category": {"MaterialName": {"quantity": X}}}
        for category, category_materials in materials.items():
            if isinstance(category_materials, dict):
                for material_name, material_data in category_materials.items():
                    material_qty = material_data.get('quantity', 1) if isinstance(material_data, dict) else 1
                    
                    if material_name in self.materials:
                        material_obj = self.materials[material_name]
                        
                        # Available in inventory (free)
                        available_free = self.inventory.get(material_name, 0)
                        
                        if available_free >= material_qty:
                            # Can fulfill from inventory for free
                            cost = 0
                        elif material_name in self.blueprints:
                            # Can produce this material
                            needed_after_inventory = max(0, material_qty - available_free)
                            cost = self._calculate_recursive_cost(material_name, needed_after_inventory)
                        else:
                            # Must buy from market
                            needed_after_inventory = max(0, material_qty - available_free)
                            cost = needed_after_inventory * material_obj.sell_price
                        
                        batch_cost += cost
        
        # Calculate how many batches needed
        batches_needed = (quantity_needed + bp.amt_per_run - 1) // bp.amt_per_run  # Ceiling division
        
        return batch_cost * batches_needed
    
    def _calculate_max_producible(self, blueprint_name):
        """Calculate maximum quantity we can produce given constraints"""
        bp = self.blueprints[blueprint_name]
        max_runs = float('inf')
        
        materials = bp.get_normalized_materials()
        
        # Materials are structured as: {"Category": {"MaterialName": {"quantity": X}}}
        for category, category_materials in materials.items():
            if isinstance(category_materials, dict):
                for material_name, material_data in category_materials.items():
                    material_qty = material_data.get('quantity', 1) if isinstance(material_data, dict) else 1
                    
                    if material_qty <= 0:
                        continue
                        
                    available = self.inventory.get(material_name, 0)
                    
                    # If we can produce this material, add potential production
                    if material_name in self.blueprints:
                        # For now, assume we can produce unlimited intermediates
                        # This could be made more sophisticated
                        available += 1000000  # Large number to represent potential production
                    
                    possible_runs = available // material_qty
                    max_runs = min(max_runs, possible_runs)
        
        # Apply blueprint max constraint if exists
        if bp.max:
            max_runs = min(max_runs, bp.max)
        
        return int(max_runs * bp.amt_per_run) if max_runs != float('inf') else 0
    
    def optimize_production(self):
        """Main optimization using greedy approach with dependency resolution"""
        production_plan = defaultdict(int)
        material_usage = defaultdict(lambda: {
            'name': '',
            'used': 0,
            'from_inventory': 0,
            'category': '',
            'unit_price': 0.0,
            'total_cost': 0.0
        })
        
        total_profit = 0.0
        dependencies_needed = defaultdict(int)
        inventory_savings = defaultdict(lambda: {'amount': 0, 'category': ''})
        
        # Calculate profit per unit for all blueprints
        blueprint_profits = {}
        for bp_name in self.blueprints:
            profit = self._calculate_profit_per_unit(bp_name)
            blueprint_profits[bp_name] = profit
        
        # Sort blueprints by profit per unit (descending)
        sorted_blueprints = sorted(blueprint_profits.items(), key=lambda x: x[1], reverse=True)
        
        # Process blueprints in order of profitability, respecting dependencies
        processed = set()
        
        for bp_name, profit_per_unit in sorted_blueprints:
            if profit_per_unit <= 0:
                continue
                
            bp = self.blueprints[bp_name]
            
            # Check if we can produce this (dependencies met)
            can_produce = self._can_produce_now(bp_name, processed)
            
            if not can_produce:
                continue
            
            # Calculate how many we can produce
            max_producible = self._calculate_max_producible(bp_name)
            
            if max_producible > 0:
                # Determine optimal quantity (greedy approach)
                to_produce = max_producible
                
                # Execute production
                self._execute_production(bp_name, to_produce, production_plan, 
                                       material_usage, dependencies_needed, inventory_savings)
                
                total_profit += to_produce * bp.sell_price
                processed.add(bp_name)
        
        # Calculate true profits
        total_cost_jita = sum(
            self._calculate_jita_cost_for_production(bp_name, qty) 
            for bp_name, qty in production_plan.items() 
            if bp_name in self.blueprints
        )
        
        total_cost_with_inventory = sum(usage['total_cost'] for usage in material_usage.values())
        
        true_profit_jita = total_profit - total_cost_jita
        true_profit_inventory = total_profit - total_cost_with_inventory
        
        # Convert production plan to type_id based
        type_id_production = {}
        for bp_name, qty in production_plan.items():
            if bp_name in self.blueprints:
                bp = self.blueprints[bp_name]
                type_id_production[bp.type_id or bp.id] = qty
        
        return {
            "status": "Optimal" if production_plan else "No profitable production found",
            "total_profit": total_profit,
            "true_profit_jita": true_profit_jita,
            "true_profit_inventory": true_profit_inventory,
            "what_to_produce": type_id_production,
            "material_usage": {mat.type_id or mat.id: usage for mat_name, usage in material_usage.items() 
                             for mat in [self.materials.get(mat_name)] if mat},
            "dependencies_needed": {mat.type_id or mat.id: qty for mat_name, qty in dependencies_needed.items() 
                                  for mat in [self.materials.get(mat_name)] if mat},
            "inventory_savings": {mat.type_id or mat.id: savings for mat_name, savings in inventory_savings.items() 
                                for mat in [self.materials.get(mat_name)] if mat}
        }
    
    def _can_produce_now(self, blueprint_name, processed):
        """Check if we can produce this blueprint now (all dependencies met)"""
        for dep in self.dependencies[blueprint_name]:
            if dep not in processed and dep in self.blueprints:
                # Check if we have enough in inventory
                dep_bp = self.blueprints[dep]
                # Simplified check - assume we need at least 1 unit
                if self.inventory.get(dep, 0) < 1:
                    return False
        return True
    
    def _execute_production(self, blueprint_name, quantity, production_plan, 
                          material_usage, dependencies_needed, inventory_savings):
        """Execute production and update tracking"""
        bp = self.blueprints[blueprint_name]
        production_plan[blueprint_name] = quantity
        
        # Calculate runs needed
        runs_needed = (quantity + bp.amt_per_run - 1) // bp.amt_per_run
        
        materials = bp.get_normalized_materials()
        
        for material in materials:
            material_name = material.get('name')
            material_qty = material.get('quantity', 0)
            needed = material_qty * runs_needed
            
        # Materials are structured as: {"Category": {"MaterialName": {"quantity": X}}}
        for category, category_materials in materials.items():
            if isinstance(category_materials, dict):
                for material_name, material_data in category_materials.items():
                    material_qty = material_data.get('quantity', 1) if isinstance(material_data, dict) else 1
                    needed = material_qty * runs_needed
                    
                    if material_name in self.materials:
                        material_obj = self.materials[material_name]
                        
                        # Use inventory first
                        from_inventory = min(needed, self.inventory.get(material_name, 0))
                        to_buy = needed - from_inventory
                        
                        # Update inventory
                        if from_inventory > 0:
                            self.inventory[material_name] -= from_inventory
                            inventory_savings[material_name]['amount'] += from_inventory
                            inventory_savings[material_name]['category'] = category
                        
                        # Track usage
                        material_usage[material_name]['name'] = material_name
                        material_usage[material_name]['used'] += needed
                        material_usage[material_name]['from_inventory'] += from_inventory
                        material_usage[material_name]['category'] = category
                        material_usage[material_name]['unit_price'] = material_obj.sell_price or 0
                        material_usage[material_name]['total_cost'] += to_buy * (material_obj.sell_price or 0)
                        
                        if to_buy > 0:
                            dependencies_needed[material_name] += to_buy
    
    def _calculate_jita_cost_for_production(self, blueprint_name, quantity):
        """Calculate total cost if all materials were bought at Jita prices"""
        bp = self.blueprints[blueprint_name]
        runs_needed = (quantity + bp.amt_per_run - 1) // bp.amt_per_run
        
        total_cost = 0
        materials = bp.get_normalized_materials()
        
        for material in materials:
            # Handle both string and dict formats
            if isinstance(material, str):
                material_name = material
                material_qty = 1  # Default quantity
            elif isinstance(material, dict):
                material_name = material.get('name')
                material_qty = material.get('quantity', 1)
            else:
                continue
            
            needed = material_qty * runs_needed
            
            if material_name in self.materials:
                material_obj = self.materials[material_name]
                total_cost += needed * (material_obj.sell_price or 0)
        
        return total_cost


def optimize_with_pulp(blueprints, materials, inventory):
    """Advanced optimization using linear programming"""
    try:
        import pulp
    except ImportError:
        logger.warning("PuLP not available, falling back to greedy optimization")
        return None
    
    # Create LP problem
    prob = pulp.LpProblem("Production_Optimization", pulp.LpMaximize)
    
    # Decision variables: how many runs of each blueprint
    blueprint_vars = {}
    for bp in blueprints:
        blueprint_vars[bp.name] = pulp.LpVariable(
            f"runs_{bp.name}", 
            lowBound=0, 
            cat='Integer'
        )
    
    # Objective: maximize profit
    profit_terms = []
    for bp in blueprints:
        # Profit per run = (sell_price * amt_per_run) - material_cost
        profit_per_run = (bp.sell_price * bp.amt_per_run) - bp.material_cost
        profit_terms.append(profit_per_run * blueprint_vars[bp.name])
    
    prob += pulp.lpSum(profit_terms)
    
    # Constraints: material availability
    material_usage = defaultdict(list)
    
    for bp in blueprints:
        materials = bp.get_normalized_materials()
        for material in materials:
            # Handle both string and dict formats
            if isinstance(material, str):
                material_name = material
                material_qty = 1  # Default quantity
            elif isinstance(material, dict):
                material_name = material.get('name')
                material_qty = material.get('quantity', 1)
            else:
                continue
            
            if material_name:
                material_usage[material_name].append(
                    material_qty * blueprint_vars[bp.name]
                )
    
    # Add constraints for each material
    for material_name, usage_terms in material_usage.items():
        available = inventory.get(material_name, 0)
        if available > 0:  # Only add constraint if we have inventory
            prob += pulp.lpSum(usage_terms) <= available
    
    # Blueprint max constraints
    for bp in blueprints:
        if bp.max:
            prob += blueprint_vars[bp.name] <= bp.max
    
    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if prob.status == pulp.LpStatusOptimal:
        solution = {}
        for bp in blueprints:
            runs = int(blueprint_vars[bp.name].varValue or 0)
            if runs > 0:
                quantity = runs * bp.amt_per_run
                solution[bp.type_id or bp.id] = quantity
        return solution
    
    return None

def validate_inventory(inventory, iteration):
    """Validate inventory state"""
    for item, quantity in inventory.items():
        if quantity < 0:
            logger.warning("Negative inventory for %s: %d at iteration %d", 
                        item, quantity, iteration)
            raise ValueError(f"Negative inventory for {item}: {quantity}")