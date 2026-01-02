from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict
from app.models.tag_registry import TagRegistry, TagCategory


class TagRegistryRepository:
    """Repository for managing tag registry"""
    
    def __init__(self, db: Session):
        self.db = db

    def get_all_tags(self) -> List[Dict]:
        """Get all tags grouped by category"""
        query = text("""
            SELECT tag, category, description
            FROM tag_registry
            ORDER BY category, tag
        """)
        
        result = self.db.execute(query)
        rows = result.fetchall()
        
        tags_by_category = {
            "app": [],
            "function": [],
            "department": []
        }
        
        for row in rows:
            tags_by_category[row.category].append({
                'tag': row.tag,
                'category': row.category,
                'description': row.description
            })
        
        return tags_by_category

    def get_tag(self, tag: str) -> Optional[Dict]:
        """Get a specific tag"""
        query = text("""
            SELECT tag, category, description
            FROM tag_registry
            WHERE tag = :tag
        """)
        
        result = self.db.execute(query, {"tag": tag})
        row = result.fetchone()
        
        if not row:
            return None
        
        return {
            'tag': row.tag,
            'category': row.category,
            'description': row.description
        }

    def create_tag(
        self,
        tag: str,
        category: TagCategory,
        description: Optional[str] = None
    ) -> TagRegistry:
        """Create a new tag in registry"""
        tag_registry = TagRegistry(
            tag=tag,
            category=category,
            description=description
        )
        self.db.add(tag_registry)
        self.db.commit()
        self.db.refresh(tag_registry)
        return tag_registry

    def update_tag(
        self,
        tag: str,
        category: Optional[TagCategory] = None,
        description: Optional[str] = None
    ) -> Optional[TagRegistry]:
        """Update a tag in registry"""
        tag_registry = self.db.query(TagRegistry).filter(TagRegistry.tag == tag).first()
        if not tag_registry:
            return None
        
        if category is not None:
            tag_registry.category = category
        if description is not None:
            tag_registry.description = description
        
        self.db.commit()
        self.db.refresh(tag_registry)
        return tag_registry

    def delete_tag(self, tag: str) -> bool:
        """Delete a tag from registry"""
        tag_registry = self.db.query(TagRegistry).filter(TagRegistry.tag == tag).first()
        if not tag_registry:
            return False
        
        self.db.delete(tag_registry)
        self.db.commit()
        return True

    def validate_tags(self, tags: List[str]) -> tuple[List[str], List[str]]:
        """Validate tags against registry. Returns (valid_tags, invalid_tags)"""
        if not tags:
            return [], []
        
        # Get all valid tags from registry
        query = text("SELECT tag FROM tag_registry WHERE tag = ANY(:tags)")
        result = self.db.execute(query, {"tags": tags})
        valid_tags_in_db = {row.tag for row in result.fetchall()}
        
        valid_tags = [t for t in tags if t in valid_tags_in_db]
        invalid_tags = [t for t in tags if t not in valid_tags_in_db]
        
        return valid_tags, invalid_tags



