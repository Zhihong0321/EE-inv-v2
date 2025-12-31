from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Tuple
from datetime import datetime, timezone


class UserRepository:
    """Repository for managing users from the 'user' table with agent profile relationships"""
    
    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        """Get all users with their agent profiles, sorted by registration date"""
        # Build the query
        query = """
            SELECT 
                u.bubble_id as user_bubble_id,
                u.created_date as registration_date,
                u.linked_agent_profile,
                a.bubble_id as agent_bubble_id,
                a.name as name,
                a.contact as whatsapp_number,
                a.email as email
            FROM "user" u
            LEFT JOIN agent a ON u.linked_agent_profile = a.bubble_id
        """
        
        params = {}
        
        if search:
            query += """
                WHERE a.name ILIKE :search 
                   OR a.contact ILIKE :search 
                   OR a.email ILIKE :search
                   OR u.bubble_id ILIKE :search
            """
            params['search'] = f"%{search}%"
        
        query += " ORDER BY u.created_date DESC"
        
        # Get total count
        count_query = query.replace(
            "SELECT \n                u.bubble_id as user_bubble_id,\n                u.created_date as registration_date,\n                u.linked_agent_profile,\n                a.bubble_id as agent_bubble_id,\n                a.name as name,\n                a.contact as whatsapp_number,\n                a.email as email\n            FROM",
            "SELECT COUNT(*) FROM"
        ).split("ORDER BY")[0]
        
        total_result = self.db.execute(text(count_query), params)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query += " LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = skip
        
        result = self.db.execute(text(query), params)
        rows = result.fetchall()
        
        # Convert to list of dicts
        users = []
        for row in rows:
            users.append({
                'user_bubble_id': row.user_bubble_id,
                'agent_bubble_id': row.agent_bubble_id,
                'name': row.name,
                'whatsapp_number': row.whatsapp_number,
                'email': row.email,
                'registration_date': row.registration_date,
                'linked_agent_profile': row.linked_agent_profile,
            })
        
        return users, total

    def get_by_id(self, user_bubble_id: str) -> Optional[dict]:
        """Get user by bubble_id"""
        query = text("""
            SELECT 
                u.bubble_id as user_bubble_id,
                u.created_date as registration_date,
                u.linked_agent_profile,
                a.bubble_id as agent_bubble_id,
                a.name as name,
                a.contact as whatsapp_number,
                a.email as email
            FROM "user" u
            LEFT JOIN agent a ON u.linked_agent_profile = a.bubble_id
            WHERE u.bubble_id = :user_bubble_id
        """)
        
        result = self.db.execute(query, {"user_bubble_id": user_bubble_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        return {
            'user_bubble_id': row.user_bubble_id,
            'agent_bubble_id': row.agent_bubble_id,
            'name': row.name,
            'whatsapp_number': row.whatsapp_number,
            'email': row.email,
            'registration_date': row.registration_date,
            'linked_agent_profile': row.linked_agent_profile,
        }

    def update_user(
        self,
        user_bubble_id: str,
        name: Optional[str] = None,
        whatsapp_number: Optional[str] = None,
        email: Optional[str] = None,
        linked_agent_profile: Optional[str] = None,
    ) -> Optional[dict]:
        """Update user and/or agent profile"""
        # First, get the current user
        user = self.get_by_id(user_bubble_id)
        if not user:
            return None
        
        # If linked_agent_profile is provided, update it in user table
        if linked_agent_profile is not None:
            update_user_query = text("""
                UPDATE "user"
                SET linked_agent_profile = :linked_agent_profile,
                    updated_at = NOW()
                WHERE bubble_id = :user_bubble_id
            """)
            self.db.execute(update_user_query, {
                "linked_agent_profile": linked_agent_profile,
                "user_bubble_id": user_bubble_id
            })
        
        # Update agent profile if agent_bubble_id exists or if we're creating/updating agent
        agent_bubble_id = linked_agent_profile or user.get('linked_agent_profile')
        
        if agent_bubble_id:
            # Check if agent exists
            check_agent_query = text("SELECT bubble_id FROM agent WHERE bubble_id = :agent_bubble_id")
            agent_exists = self.db.execute(check_agent_query, {"agent_bubble_id": agent_bubble_id}).fetchone()
            
            if agent_exists:
                # Update existing agent
                update_fields = []
                update_params = {"agent_bubble_id": agent_bubble_id}
                
                if name is not None:
                    update_fields.append("name = :name")
                    update_params["name"] = name
                
                if whatsapp_number is not None:
                    update_fields.append("contact = :contact")
                    update_params["contact"] = whatsapp_number
                
                if email is not None:
                    update_fields.append("email = :email")
                    update_params["email"] = email
                
                if update_fields:
                    update_fields.append("updated_at = NOW()")
                    update_agent_query = text(f"""
                        UPDATE agent
                        SET {', '.join(update_fields)}
                        WHERE bubble_id = :agent_bubble_id
                    """)
                    self.db.execute(update_agent_query, update_params)
            else:
                # Create new agent profile
                # Note: We need to generate a bubble_id if creating new agent
                # For now, we'll use the linked_agent_profile as bubble_id
                insert_agent_query = text("""
                    INSERT INTO agent (bubble_id, name, contact, email, created_at, updated_at)
                    VALUES (:agent_bubble_id, :name, :contact, :email, NOW(), NOW())
                """)
                self.db.execute(insert_agent_query, {
                    "agent_bubble_id": agent_bubble_id,
                    "name": name or "",
                    "contact": whatsapp_number or "",
                    "email": email or ""
                })
        
        self.db.commit()
        
        # Return updated user
        return self.get_by_id(user_bubble_id)

    def create_user(
        self,
        name: str,
        whatsapp_number: Optional[str] = None,
        email: Optional[str] = None,
        linked_agent_profile: Optional[str] = None,
    ) -> dict:
        """Create a new user with agent profile"""
        import time
        
        # Generate bubble_id for user (format: timestamp + random)
        import random
        timestamp = int(time.time() * 1000)
        random_part = random.randint(100000000000000000, 999999999999999999)
        user_bubble_id = f"{timestamp}x{random_part}"
        
        # If linked_agent_profile is provided, use it; otherwise create new agent
        if not linked_agent_profile:
            # Create new agent profile
            agent_timestamp = int(time.time() * 1000)
            agent_random = random.randint(100000000000000000, 999999999999999999)
            linked_agent_profile = f"{agent_timestamp}x{agent_random}"
            
            # Insert agent first
            insert_agent_query = text("""
                INSERT INTO agent (bubble_id, name, contact, email, created_at, updated_at, created_date)
                VALUES (:agent_bubble_id, :name, :contact, :email, NOW(), NOW(), NOW())
            """)
            self.db.execute(insert_agent_query, {
                "agent_bubble_id": linked_agent_profile,
                "name": name,
                "contact": whatsapp_number or "",
                "email": email or ""
            })
        
        # Insert user
        insert_user_query = text("""
            INSERT INTO "user" (bubble_id, linked_agent_profile, created_date, created_at, updated_at)
            VALUES (:user_bubble_id, :linked_agent_profile, NOW(), NOW(), NOW())
        """)
        self.db.execute(insert_user_query, {
            "user_bubble_id": user_bubble_id,
            "linked_agent_profile": linked_agent_profile
        })
        
        self.db.commit()
        
        # Return created user
        return self.get_by_id(user_bubble_id)

