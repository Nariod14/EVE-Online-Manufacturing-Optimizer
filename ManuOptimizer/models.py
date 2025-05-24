from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Blueprint(db.Model):
    __tablename__ = 'blueprint'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    materials = db.Column(db.JSON, nullable=False)
    sell_price = db.Column(db.Float, nullable=False)
    max = db.Column(db.Integer, nullable=True)
    material_cost = db.Column(db.Float, nullable=False)
    tier = db.Column(db.String(10), nullable=False, default="T1")  # "T1" or "T2"
    __mapper_args__ = {
        "polymorphic_identity": "T1",
        "polymorphic_on": tier
    }

class BlueprintT2(Blueprint):
    __tablename__ = 'blueprint_t2'
    id = db.Column(db.Integer, db.ForeignKey('blueprint.id'), primary_key=True)
    invention_chance = db.Column(db.Float, nullable=False)
    __mapper_args__ = {
        "polymorphic_identity": "T2",
    }

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
