import json
from contextvars import ContextVar
from sqlalchemy import event
from sqlalchemy.orm import Session
from datetime import datetime

# ContextVariables to store request-scoped user info
current_user_id: ContextVar[int] = ContextVar("current_user_id", default=None)
current_ip_address: ContextVar[str] = ContextVar("current_ip_address", default=None)
# To prevent infinite loops or logging unwanted models
AUDIT_EXCLUDE_TABLES = {"audit_logs", "reminders", "voyage_task_logs"}

def set_audit_context(user_id: int = None, ip_address: str = None):
    current_user_id.set(user_id)
    current_ip_address.set(ip_address)

def log_action(db: Session, action: str, table_name: str = None, target_id: str = None,
               old_value: dict = None, new_value: dict = None, user_id: int = None, ip_address: str = None):
    from models import AuditLog
    
    uid = user_id if user_id is not None else current_user_id.get()
    ip = ip_address if ip_address is not None else current_ip_address.get()
    
    audit_entry = AuditLog(
        user_id=uid,
        action=action,
        table_name=table_name,
        target_id=target_id,
        old_value=json.dumps(old_value, ensure_ascii=False, default=str) if old_value else None,
        new_value=json.dumps(new_value, ensure_ascii=False, default=str) if new_value else None,
        timestamp=datetime.now(),
        ip_address=ip
    )
    db.add(audit_entry)

def object_as_dict(obj):
    """Convert SQLAlchemy model instance to dict"""
    return {c.key: getattr(obj, c.key) for c in obj.__table__.columns}

def register_audit_events(engine):
    
    @event.listens_for(Session, "before_flush")
    def receive_before_flush(session, flush_context, instances):
        from models import AuditLog
        
        # Prevent self-logging and infinite loop
        audit_entries = []
        uid = current_user_id.get()
        ip = current_ip_address.get()
        
        for obj in session.new:
            if getattr(obj, "__tablename__", None) in AUDIT_EXCLUDE_TABLES:
                continue
            if isinstance(obj, AuditLog):
                continue
                
            state = session.info.get('audit_state', {})
            # target_id might not be generated yet during flush if auto-increment
            # but usually it's better to get the inserted id after commit.
            # For simplicity, we capture the data now.
            new_val = object_as_dict(obj)
            audit_entries.append(AuditLog(
                user_id=uid,
                action="CREATE",
                table_name=obj.__tablename__,
                target_id=str(getattr(obj, "id", None)), 
                old_value=None,
                new_value=json.dumps(new_val, ensure_ascii=False, default=str),
                ip_address=ip
            ))

        for obj in session.dirty:
            if getattr(obj, "__tablename__", None) in AUDIT_EXCLUDE_TABLES:
                continue
            if isinstance(obj, AuditLog):
                continue
            
            # Use `get_history` to get changes
            from sqlalchemy.orm.attributes import get_history
            changes = {}
            for col in obj.__table__.columns:
                hist = get_history(obj, col.name)
                if hist.has_changes():
                    changes[col.name] = {
                        "old": hist.deleted[0] if hist.deleted else None,
                        "new": hist.added[0] if hist.added else getattr(obj, col.name)
                    }
            
            if changes:
                old_val = {k: v["old"] for k, v in changes.items()}
                new_val = {k: v["new"] for k, v in changes.items()}
                
                audit_entries.append(AuditLog(
                    user_id=uid,
                    action="UPDATE",
                    table_name=obj.__tablename__,
                    target_id=str(getattr(obj, "id", None)),
                    old_value=json.dumps(old_val, ensure_ascii=False, default=str),
                    new_value=json.dumps(new_val, ensure_ascii=False, default=str),
                    ip_address=ip
                ))

        for obj in session.deleted:
            if getattr(obj, "__tablename__", None) in AUDIT_EXCLUDE_TABLES:
                continue
            if isinstance(obj, AuditLog):
                continue
            
            old_val = object_as_dict(obj)
            audit_entries.append(AuditLog(
                user_id=uid,
                action="DELETE",
                table_name=obj.__tablename__,
                target_id=str(getattr(obj, "id", None)),
                old_value=json.dumps(old_val, ensure_ascii=False, default=str),
                new_value=None,
                ip_address=ip
            ))
            
        if audit_entries:
            session.add_all(audit_entries)
