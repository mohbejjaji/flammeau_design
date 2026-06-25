from core.database import SessionLocal

class Repository:
    def __init__(self, model):
        self.model = model
        self.db = SessionLocal()

    def add(self, obj):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_all(self):
        return self.db.query(self.model).all()

    def get_by_id(self, obj_id):
        return self.db.query(self.model).get(obj_id)

    def delete(self, obj):
        self.db.delete(obj)
        self.db.commit()