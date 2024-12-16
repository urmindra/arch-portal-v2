from psycopg2.extras import RealDictCursor
from .database import db
from datetime import datetime
import json
from collections import defaultdict

class EntityManager:
    @staticmethod
    def create_entity(name, entity_type, description="", metadata=None):
        """Create a new entity with proper metadata handling."""
        db.ensure_connection()
        with db.conn.cursor() as cur:
            try:
                # Ensure metadata is a valid dictionary
                if metadata is not None:
                    if not isinstance(metadata, dict):
                        raise ValueError("Metadata must be a dictionary")
                    # Convert all values to strings for consistent handling
                    metadata = {k: str(v) if not isinstance(v, (list, dict)) else v 
                              for k, v in metadata.items()}
                
                json_metadata = json.dumps(metadata) if metadata else None
                
                cur.execute(
                    "INSERT INTO entities (name, type, description, metadata) VALUES (%s, %s, %s, %s::jsonb) RETURNING id",
                    (name, entity_type, description, json_metadata)
                )
                entity_id = cur.fetchone()[0]
                db.conn.commit()
                return entity_id
            except (json.JSONDecodeError, ValueError) as e:
                db.conn.rollback()
                raise ValueError(f"Invalid metadata format: {str(e)}")
            except Exception as e:
                db.conn.rollback()
                raise Exception(f"Error creating entity: {str(e)}")

    @staticmethod
    def get_tags():
        db.ensure_connection()
        with db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute("SELECT name FROM tags ORDER BY name")
                return [tag['name'] for tag in cur.fetchall()]
            except Exception as e:
                print(f"Error fetching tags: {str(e)}")
                return []

    @staticmethod
    def add_tag(entity_id, tag_name):
        db.ensure_connection()
        with db.conn.cursor() as cur:
            try:
                # First, insert or get the tag
                cur.execute(
                    '''
                    INSERT INTO tags (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    ''',
                    (tag_name,)
                )
                tag_id = cur.fetchone()[0]
                
                # If entity_id is provided, create the entity-tag relationship
                if entity_id is not None:
                    cur.execute(
                        '''
                        INSERT INTO entity_tags (entity_id, tag_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        ''',
                        (entity_id, tag_id)
                    )
                
                db.conn.commit()
                return tag_id
            except Exception as e:
                db.conn.rollback()
                raise Exception(f"Error adding tag: {str(e)}")

    @staticmethod
    def get_entities(entity_type=None, search_term=None, search_type="Name", tags=None, date_filter=None, date_to=None, relationship_types=None):
        """Get entities with optional filtering.
        
        Args:
            entity_type: Filter by entity type
            search_term: Search term for name/description
            search_type: Type of search (Name/Description/All)
            tags: Filter by tags
            date_filter: Filter entities created after this date
            date_to: Filter entities created before this date
            relationship_types: Filter by relationship types
        """
        db.ensure_connection()
        with db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                query = '''
                    SELECT DISTINCT e.*, array_agg(t.name) FILTER (WHERE t.name IS NOT NULL) as tags
                    FROM entities e
                    LEFT JOIN entity_tags et ON e.id = et.entity_id
                    LEFT JOIN tags t ON et.tag_id = t.id
                '''
                
                conditions = []
                params = []
                
                if entity_type and entity_type != "All":
                    conditions.append("e.type = %s")
                    params.append(entity_type)
                    
                if search_term:
                    if search_type == "Name":
                        conditions.append("e.name ILIKE %s")
                        params.append(f"%{search_term}%")
                    elif search_type == "Description":
                        conditions.append("e.description ILIKE %s")
                        params.append(f"%{search_term}%")
                    else:  # All Fields
                        conditions.append("(e.name ILIKE %s OR e.description ILIKE %s)")
                        params.extend([f"%{search_term}%", f"%{search_term}%"])
                        
                if date_filter:
                    conditions.append("e.created_at >= %s")
                    params.append(date_filter)
                
                if date_to:
                    conditions.append("e.created_at <= %s")
                    params.append(date_to)
                    
                if tags:
                    placeholders = ', '.join(['%s'] * len(tags))
                    conditions.append(f"t.name IN ({placeholders})")
                    params.extend(tags)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                    
                query += " GROUP BY e.id ORDER BY e.name"
                
                cur.execute(query, params)
                return cur.fetchall()
                
            except Exception as e:
                print(f"Error fetching entities: {str(e)}")
                return []

    @staticmethod
    def update_entity(entity_id, description=None):
        db.ensure_connection()
        with db.conn.cursor() as cur:
            try:
                if description is not None:
                    cur.execute(
                        "UPDATE entities SET description = %s WHERE id = %s",
                        (description, entity_id)
                    )
                db.conn.commit()
            except Exception as e:
                db.conn.rollback()
                raise Exception(f"Error updating entity: {str(e)}")

    @staticmethod
    def update_entity_tags(entity_id, new_tags):
        db.ensure_connection()
        with db.conn.cursor() as cur:
            try:
                # Remove existing tags
                cur.execute("DELETE FROM entity_tags WHERE entity_id = %s", (entity_id,))
                
                # Add new tags
                for tag_name in new_tags:
                    # First ensure the tag exists
                    cur.execute(
                        '''
                        INSERT INTO tags (name)
                        VALUES (%s)
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                        ''',
                        (tag_name,)
                    )
                    tag_id = cur.fetchone()[0]
                    
                    # Create entity-tag relationship
                    cur.execute(
                        "INSERT INTO entity_tags (entity_id, tag_id) VALUES (%s, %s)",
                        (entity_id, tag_id)
                    )
                
                db.conn.commit()
            except Exception as e:
                db.conn.rollback()
                raise Exception(f"Error updating entity tags: {str(e)}")

    @staticmethod
    def delete_entity(entity_id):
        db.ensure_connection()
        with db.conn.cursor() as cur:
            try:
                cur.execute("DELETE FROM entities WHERE id = %s", (entity_id,))
                db.conn.commit()
            except Exception as e:
                db.conn.rollback()
                raise Exception(f"Error deleting entity: {str(e)}")

    @staticmethod
    def get_relationships(entity_type=None, search_term=None, relationship_types=None):
        db.ensure_connection()
        with db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                query = '''
                    SELECT r.*, 
                           s.name as source_name, 
                           t.name as target_name
                    FROM relationships r
                    JOIN entities s ON r.source_id = s.id
                    JOIN entities t ON r.target_id = t.id
                '''
                
                conditions = []
                params = []
                
                if entity_type and entity_type != "All":
                    conditions.append("(s.type = %s OR t.type = %s)")
                    params.extend([entity_type, entity_type])
                    
                if search_term:
                    conditions.append("(s.name ILIKE %s OR t.name ILIKE %s)")
                    params.extend([f"%{search_term}%", f"%{search_term}%"])
                    
                if relationship_types:
                    placeholders = ', '.join(['%s'] * len(relationship_types))
                    conditions.append(f"r.relationship_type IN ({placeholders})")
                    params.extend(relationship_types)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                    
                query += " ORDER BY r.created_at DESC"
                
                cur.execute(query, params)
                return cur.fetchall()
                
            except Exception as e:
                print(f"Error fetching relationships: {str(e)}")
                return []

    @staticmethod
    def get_entity_relationships(entity_id):
        db.ensure_connection()
        with db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute("""
                    SELECT r.id,
                           r.relationship_type, 
                           CASE WHEN r.source_id = %s THEN t.name ELSE s.name END as related_entity_name,
                           CASE WHEN r.source_id = %s THEN t.id ELSE s.id END as related_entity_id,
                           r.source_id = %s as is_source
                    FROM relationships r
                    JOIN entities s ON r.source_id = s.id
                    JOIN entities t ON r.target_id = t.id
                    WHERE r.source_id = %s OR r.target_id = %s
                """, (entity_id, entity_id, entity_id, entity_id, entity_id))
                return cur.fetchall()
            except Exception as e:
                print(f"Error fetching relationships: {str(e)}")
                return []

    @staticmethod
    def get_entity_tags(entity_id):
        db.ensure_connection()
        with db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute("""
                    SELECT t.* FROM tags t
                    JOIN entity_tags et ON t.id = et.tag_id
                    WHERE et.entity_id = %s
                """, (entity_id,))
                return cur.fetchall()
            except Exception as e:
                print(f"Error fetching entity tags: {str(e)}")
                return []

    @staticmethod
    def create_relationship(source_id, target_id, relationship_type):
        db.ensure_connection()
        with db.conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO relationships (source_id, target_id, relationship_type) VALUES (%s, %s, %s)",
                    (source_id, target_id, relationship_type)
                )
                db.conn.commit()
            except Exception as e:
                db.conn.rollback()
                raise Exception(f"Error creating relationship: {str(e)}")

    @staticmethod
    def update_relationship(relationship_id, relationship_type):
        db.ensure_connection()
        with db.conn.cursor() as cur:
            try:
                cur.execute(
                    "UPDATE relationships SET relationship_type = %s WHERE id = %s",
                    (relationship_type, relationship_id)
                )
                db.conn.commit()
            except Exception as e:
                db.conn.rollback()
                raise Exception(f"Error updating relationship: {str(e)}")

    @staticmethod
    def delete_relationship(source_id, target_name):
        db.ensure_connection()
        with db.conn.cursor() as cur:
            try:
                # First get the target entity id
                cur.execute("SELECT id FROM entities WHERE name = %s", (target_name,))
                target = cur.fetchone()
                if target:
                    target_id = target[0]
                    # Delete the relationship
                    cur.execute(
                        "DELETE FROM relationships WHERE (source_id = %s AND target_id = %s) OR (source_id = %s AND target_id = %s)",
                        (source_id, target_id, target_id, source_id)
                    )
                    db.conn.commit()
            except Exception as e:
                db.conn.rollback()
                raise Exception(f"Error deleting relationship: {str(e)}")
    @staticmethod
    def delete_multiple_entities(entity_ids):
        """Delete multiple entities at once."""
        db.ensure_connection()
        with db.conn.cursor() as cur:
            try:
                cur.execute(
                    "DELETE FROM entities WHERE id = ANY(%s)",
                    (entity_ids,)
                )
                db.conn.commit()
            except Exception as e:
                db.conn.rollback()
                raise Exception(f"Error deleting multiple entities: {str(e)}")

    @staticmethod
    def delete_multiple_relationships(relationship_ids):
        """Delete multiple relationships at once."""
        db.ensure_connection()
        with db.conn.cursor() as cur:
            try:
                cur.execute(
                    "DELETE FROM relationships WHERE id = ANY(%s)",
                    (relationship_ids,)
                )
                db.conn.commit()
            except Exception as e:
                db.conn.rollback()
                raise Exception(f"Error deleting multiple relationships: {str(e)}")
