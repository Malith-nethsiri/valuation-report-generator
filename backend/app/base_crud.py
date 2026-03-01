"""Generic CRUD operations for SQLAlchemy models with user ownership."""
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Type


def verify_ownership(db: Session, model, entity_id: int, user_id: int, entity_name: str):
    """Verify that an entity exists and belongs to the user.

    Fail-closed: raises 404 if the entity has no user_id attribute, does not
    exist, or belongs to a different user. Never silently grants access.
    """
    entity = db.query(model).filter(model.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    if not hasattr(entity, 'user_id') or entity.user_id != user_id:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity


class BaseCRUD:
    """Generic CRUD operations for SQLAlchemy models with ownership."""

    def __init__(self, model: Type, entity_name: str):
        self.model = model
        self.entity_name = entity_name

    def create(self, db: Session, data: dict, user_id: int, **extra_fields):
        entity = self.model(**data, user_id=user_id, **extra_fields)
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    def get(self, db: Session, entity_id: int, user_id: int):
        return verify_ownership(db, self.model, entity_id, user_id, self.entity_name)

    def get_user_list(self, db: Session, user_id: int, skip: int = 0, limit: int = 100):
        query = db.query(self.model).filter(self.model.user_id == user_id)
        if hasattr(self.model, 'created_at'):
            query = query.order_by(self.model.created_at.desc())
        return query.offset(skip).limit(limit).all()

    def update(self, db: Session, entity_id: int, user_id: int, data: dict):
        entity = self.get(db, entity_id, user_id)
        protected = {'id', 'user_id'}
        for key, value in data.items():
            if key not in protected and hasattr(entity, key):
                setattr(entity, key, value)
        db.commit()
        db.refresh(entity)
        return entity

    def delete(self, db: Session, entity_id: int, user_id: int):
        entity = self.get(db, entity_id, user_id)
        db.delete(entity)
        db.commit()
        return True
