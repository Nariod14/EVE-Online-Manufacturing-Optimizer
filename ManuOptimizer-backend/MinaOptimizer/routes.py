# from flask import Blueprint, jsonify
# from models import Blueprint as BP, Material
# from .minapp import build_mining_plan

# mining_planner = Blueprint('mining_planner', __name__)

# @mining_planner.route('/mining_plan', methods=['GET'])
# def mining_plan():
#     blueprints = BP.query.all()
#     materials = {m.name: m.quantity for m in Material.query.all()}

#     if not blueprints or not materials:
#         return jsonify({"status": "No mining plan possible: missing data"}), 400

#     try:
#         plan = build_mining_plan(blueprints, materials)
#         return jsonify(plan), 200
#     except Exception as e:
#         import traceback
#         print(traceback.format_exc())
#         return jsonify({"error": str(e)}), 500
