import pytest
from datetime import datetime
from app.models import AdminAuditLog, AdminActionType, User # Import necessary models

# Note: These tests focus on the model's attributes and methods
# without involving database interactions.

def test_admin_audit_log_creation():
    """Test creating an AdminAuditLog instance sets attributes correctly."""
    admin_id = 1
    action = AdminActionType.GAME_DELETE
    target_type = "game"
    target_id = 5
    prev_state = {"status": "UPCOMING"}
    new_state = {"status": "DELETED", "deleted_by": admin_id}
    reason = "Test deletion"

    log_entry = AdminAuditLog(
        admin_id=admin_id,
        action_type=action,
        target_type=target_type,
        target_id=target_id,
        previous_state=prev_state,
        new_state=new_state,
        reason=reason
        # created_at has a database default
    )

    assert log_entry.admin_id == admin_id
    assert log_entry.action_type == action
    assert log_entry.target_type == target_type
    assert log_entry.target_id == target_id
    assert log_entry.previous_state == prev_state
    assert log_entry.new_state == new_state
    assert log_entry.reason == reason
    # Database default is not set on instantiation
    assert log_entry.created_at is None

def test_admin_audit_log_repr():
    """Test the __repr__ method for the AdminAuditLog model."""
    log_entry = AdminAuditLog(
        id=101, # Manually set for testing repr
        admin_id=2,
        action_type=AdminActionType.MATCH_UNAPPROVE,
        target_type="match",
        target_id=50
    )
    expected_repr = '<AdminAuditLog id=101 action=MATCH_UNAPPROVE target=match:50>'
    assert repr(log_entry) == expected_repr