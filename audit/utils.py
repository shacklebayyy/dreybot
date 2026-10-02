from .models import AuditLog

def log_audit(user_profile=None, action: str = '', object_type: str = '', object_id: str = '', ip_address: str = None, metadata: dict = None):
    try:
        AuditLog.objects.create(
            user_profile=user_profile,
            action=action,
            object_type=object_type,
            object_id=str(object_id) if object_id else '',
            ip_address=ip_address,
            metadata=metadata or {}
        )
    except Exception as e:
        print(f"Failed to record audit log: {e}")
