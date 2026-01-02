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
        sort_by: Optional[str] = "registration_date",
        sort_order: Optional[str] = "desc",
    ) -> Tuple[List[dict], int]:
        """Get all users with their agent profiles, sorted by specified column"""
        # Build the query
        # Extract email from authentication JSON as fallback if agent data is NULL
        # Authentication JSON structure: {"email": {"email": "xxx@gmail.com"}}
        query = """
            SELECT 
                u.bubble_id as user_bubble_id,
                u.created_date as registration_date,
                u.linked_agent_profile,
                u.access_level as access_level,
                u.authentication,
                a.bubble_id as agent_bubble_id,
                COALESCE(
                    a.name,
                    CASE 
                        WHEN u.authentication IS NOT NULL 
                             AND u.authentication::jsonb->'email' IS NOT NULL
                             AND u.authentication::jsonb->'email'->>'email' IS NOT NULL
                        THEN u.authentication::jsonb->'email'->>'email'
                        ELSE NULL
                    END
                ) as name,
                COALESCE(
                    a.contact,
                    CASE 
                        WHEN u.authentication IS NOT NULL 
                             AND u.authentication::jsonb->'whatsapp' IS NOT NULL
                        THEN 
                            CASE 
                                WHEN jsonb_typeof(u.authentication::jsonb->'whatsapp') = 'object'
                                THEN COALESCE(
                                    u.authentication::jsonb->'whatsapp'->>'number',
                                    u.authentication::jsonb->'whatsapp'->>'phone'
                                )
                                ELSE u.authentication::jsonb->>'whatsapp'
                            END
                        ELSE NULL
                    END,
                    CASE 
                        WHEN u.authentication IS NOT NULL 
                             AND u.authentication::jsonb->>'phone' IS NOT NULL
                        THEN u.authentication::jsonb->>'phone'
                        ELSE NULL
                    END
                ) as whatsapp_number,
                COALESCE(
                    a.email,
                    CASE 
                        WHEN u.authentication IS NOT NULL 
                             AND u.authentication::jsonb->'email' IS NOT NULL
                             AND u.authentication::jsonb->'email'->>'email' IS NOT NULL
                        THEN u.authentication::jsonb->'email'->>'email'
                        ELSE NULL
                    END
                ) as email
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
                   OR (u.authentication IS NOT NULL 
                       AND u.authentication::jsonb->'email'->>'email' ILIKE :search)
            """
            params['search'] = f"%{search}%"
        
        # Validate and set sort column
        # Use the same COALESCE logic for sorting
        if sort_by == "name":
            sort_column = """COALESCE(a.name,
                CASE 
                    WHEN u.authentication IS NOT NULL 
                         AND u.authentication::jsonb->'email' IS NOT NULL
                         AND u.authentication::jsonb->'email'->>'email' IS NOT NULL
                    THEN u.authentication::jsonb->'email'->>'email'
                    ELSE NULL
                END
            )"""
        elif sort_by == "email":
            sort_column = """COALESCE(a.email,
                CASE 
                    WHEN u.authentication IS NOT NULL 
                         AND u.authentication::jsonb->'email' IS NOT NULL
                         AND u.authentication::jsonb->'email'->>'email' IS NOT NULL
                    THEN u.authentication::jsonb->'email'->>'email'
                    ELSE NULL
                END
            )"""
        elif sort_by == "whatsapp_number":
            sort_column = "a.contact"
        else:
            sort_column = "u.created_date"
        
        # Safely handle sort_order (defensive programming)
        if sort_order and sort_order.lower() == "desc":
            sort_direction = "DESC"
        else:
            sort_direction = "ASC"
        
        # Handle NULL values in sorting (put NULLs last)
        if sort_by in ["name", "email", "whatsapp_number"]:
            query += f" ORDER BY {sort_column} {sort_direction} NULLS LAST"
        else:
            query += f" ORDER BY {sort_column} {sort_direction}"
        
        # Get total count - build count query separately
        count_query = """
            SELECT COUNT(*) 
            FROM "user" u
            LEFT JOIN agent a ON u.linked_agent_profile = a.bubble_id
        """
        if search:
            count_query += """
                WHERE a.name ILIKE :search 
                   OR a.contact ILIKE :search 
                   OR a.email ILIKE :search
                   OR u.bubble_id ILIKE :search
                   OR (u.authentication IS NOT NULL 
                       AND u.authentication::jsonb->'email'->>'email' ILIKE :search)
            """
        
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
                'access_level': list(row.access_level) if row.access_level else [],
            })
        
        return users, total

    def get_by_id(self, user_bubble_id: str) -> Optional[dict]:
        """Get user by bubble_id"""
        query = text("""
            SELECT 
                u.bubble_id as user_bubble_id,
                u.created_date as registration_date,
                u.linked_agent_profile,
                u.access_level as access_level,
                u.authentication,
                a.bubble_id as agent_bubble_id,
                COALESCE(
                    a.name,
                    CASE 
                        WHEN u.authentication IS NOT NULL 
                             AND u.authentication::jsonb->'email' IS NOT NULL
                             AND u.authentication::jsonb->'email'->>'email' IS NOT NULL
                        THEN u.authentication::jsonb->'email'->>'email'
                        ELSE NULL
                    END
                ) as name,
                COALESCE(
                    a.contact,
                    CASE 
                        WHEN u.authentication IS NOT NULL 
                             AND u.authentication::jsonb->'whatsapp' IS NOT NULL
                        THEN 
                            CASE 
                                WHEN jsonb_typeof(u.authentication::jsonb->'whatsapp') = 'object'
                                THEN COALESCE(
                                    u.authentication::jsonb->'whatsapp'->>'number',
                                    u.authentication::jsonb->'whatsapp'->>'phone'
                                )
                                ELSE u.authentication::jsonb->>'whatsapp'
                            END
                        ELSE NULL
                    END,
                    CASE 
                        WHEN u.authentication IS NOT NULL 
                             AND u.authentication::jsonb->>'phone' IS NOT NULL
                        THEN u.authentication::jsonb->>'phone'
                        ELSE NULL
                    END
                ) as whatsapp_number,
                COALESCE(
                    a.email,
                    CASE 
                        WHEN u.authentication IS NOT NULL 
                             AND u.authentication::jsonb->'email' IS NOT NULL
                             AND u.authentication::jsonb->'email'->>'email' IS NOT NULL
                        THEN u.authentication::jsonb->'email'->>'email'
                        ELSE NULL
                    END
                ) as email
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
            'access_level': list(row.access_level) if row.access_level else [],
        }

    def update_user(
        self,
        user_bubble_id: str,
        name: Optional[str] = None,
        whatsapp_number: Optional[str] = None,
        email: Optional[str] = None,
        linked_agent_profile: Optional[str] = None,
        access_level: Optional[List[str]] = None,
    ) -> Optional[dict]:
        """Update user and/or agent profile"""
        # First, get the current user
        user = self.get_by_id(user_bubble_id)
        if not user:
            return None
        
        # Build update fields dynamically
        update_fields = []
        update_params = {"user_bubble_id": user_bubble_id}
        
        if linked_agent_profile is not None:
            update_fields.append("linked_agent_profile = :linked_agent_profile")
            update_params["linked_agent_profile"] = linked_agent_profile
        
        if access_level is not None:
            update_fields.append("access_level = :access_level")
            update_params["access_level"] = access_level
        
        if update_fields:
            update_fields.append("updated_at = NOW()")
            update_user_query = text(f"""
                UPDATE "user"
                SET {', '.join(update_fields)}
                WHERE bubble_id = :user_bubble_id
            """)
            self.db.execute(update_user_query, update_params)
        
        # Update agent profile - create if needed
        # If we're updating name/whatsapp/email, we need an agent profile
        needs_agent_update = name is not None or whatsapp_number is not None or email is not None
        
        if needs_agent_update:
            agent_bubble_id = linked_agent_profile or user.get('linked_agent_profile')
            
            # If no agent_bubble_id exists, create a new one
            if not agent_bubble_id:
                import time
                import random
                timestamp = int(time.time() * 1000)
                random_part = random.randint(100000000000000000, 999999999999999999)
                agent_bubble_id = f"{timestamp}x{random_part}"
                
                # Update user's linked_agent_profile
                update_user_link_query = text("""
                    UPDATE "user"
                    SET linked_agent_profile = :agent_bubble_id,
                        updated_at = NOW()
                    WHERE bubble_id = :user_bubble_id
                """)
                self.db.execute(update_user_link_query, {
                    "agent_bubble_id": agent_bubble_id,
                    "user_bubble_id": user_bubble_id
                })
            
            # Check if agent exists
            check_agent_query = text("SELECT bubble_id FROM agent WHERE bubble_id = :agent_bubble_id")
            agent_exists = self.db.execute(check_agent_query, {"agent_bubble_id": agent_bubble_id}).fetchone()
            
            if agent_exists:
                # Update existing agent
                # Use a flag to track if we need to update (including clearing fields with None)
                update_fields = []
                update_params = {"agent_bubble_id": agent_bubble_id}
                
                # Check if any field is being updated (including None to clear)
                if name is not None:
                    update_fields.append("name = :name")
                    update_params["name"] = name if name else None
                
                if whatsapp_number is not None:
                    update_fields.append("contact = :contact")
                    update_params["contact"] = whatsapp_number if whatsapp_number else None
                
                if email is not None:
                    update_fields.append("email = :email")
                    update_params["email"] = email if email else None
                
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
                insert_agent_query = text("""
                    INSERT INTO agent (bubble_id, name, contact, email, created_at, updated_at, created_date)
                    VALUES (:agent_bubble_id, :name, :contact, :email, NOW(), NOW(), NOW())
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

    def update_user_tags(
        self,
        user_bubble_id: str,
        tags: List[str],
    ) -> Optional[dict]:
        """Update user access_level tags"""
        user = self.get_by_id(user_bubble_id)
        if not user:
            return None
        
        # Update access_level in user table
        update_query = text("""
            UPDATE "user"
            SET access_level = :access_level,
                updated_at = NOW()
            WHERE bubble_id = :user_bubble_id
        """)
        self.db.execute(update_query, {
            "access_level": tags,
            "user_bubble_id": user_bubble_id
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

