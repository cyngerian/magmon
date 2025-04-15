# Admin Game Management Implementation Plan

## Overview
Add comprehensive game management capabilities for admins with full audit logging of all administrative actions.

## Database Changes

### 1. Admin Audit Log Table
```sql
CREATE TABLE admin_audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL,  -- e.g., 'game_unapprove', 'game_delete', 'password_reset'
    target_type VARCHAR(50) NOT NULL,  -- e.g., 'game', 'match', 'user'
    target_id INTEGER NOT NULL,        -- ID of the affected record
    previous_state JSONB,              -- Snapshot of data before change
    new_state JSONB,                   -- Snapshot of data after change
    reason TEXT,                       -- Admin's reason for the change
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient querying
CREATE INDEX idx_admin_audit_target ON admin_audit_logs(target_type, target_id);
CREATE INDEX idx_admin_audit_admin ON admin_audit_logs(admin_id);
```

### 2. Game Model Updates
```sql
ALTER TABLE games ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE games ADD COLUMN deleted_by_id INTEGER REFERENCES users(id);
ALTER TABLE games ADD COLUMN last_admin_action VARCHAR(50);
ALTER TABLE games ADD COLUMN last_admin_action_at TIMESTAMP;
```

### 3. Match Model Updates
```sql
ALTER TABLE matches ADD COLUMN unapproved_at TIMESTAMP;
ALTER TABLE matches ADD COLUMN unapproved_by_id INTEGER REFERENCES users(id);
ALTER TABLE matches ADD COLUMN unsubmitted_at TIMESTAMP;
ALTER TABLE matches ADD COLUMN unsubmitted_by_id INTEGER REFERENCES users(id);
```

## Backend Components

### 1. Admin Audit Service
```python
class AdminAuditService:
    @staticmethod
    def log_action(admin_id, action_type, target_type, target_id, previous_state, new_state, reason=None):
        log = AdminAuditLog(
            admin_id=admin_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason
        )
        db.session.add(log)
        db.session.commit()
```

### 2. New Admin API Endpoints

#### Game Management
```python
@bp.route('/admin/games/<int:game_id>', methods=['DELETE'])
@admin_required
def delete_game(game_id):
    """Soft delete a game and all related data"""

@bp.route('/admin/games/<int:game_id>/restore', methods=['POST'])
@admin_required
def restore_game(game_id):
    """Restore a soft-deleted game"""

@bp.route('/admin/matches/<int:match_id>/unapprove', methods=['POST'])
@admin_required
def unapprove_match(match_id):
    """Remove approval from a match"""

@bp.route('/admin/matches/<int:match_id>/unsubmit', methods=['POST'])
@admin_required
def unsubmit_match(match_id):
    """Reset a match to unsubmitted state"""
```

#### Audit Log Access
```python
@bp.route('/admin/audit-logs', methods=['GET'])
@admin_required
def get_audit_logs():
    """Get paginated audit logs with filtering"""

@bp.route('/admin/audit-logs/<int:target_id>', methods=['GET'])
@admin_required
def get_target_audit_logs(target_id):
    """Get audit history for a specific target"""
```

## Frontend Components

### 1. Admin Game Management Page
- List of all games with enhanced admin actions
- Filters for game status (including deleted)
- Bulk action support
- Audit log viewer

```typescript
interface AdminGameAction {
    gameId: number;
    action: 'delete' | 'restore' | 'unapprove' | 'unsubmit';
    reason: string;
}

interface AuditLogEntry {
    id: number;
    adminUsername: string;
    actionType: string;
    targetType: string;
    targetId: number;
    previousState: any;
    newState: any;
    reason: string;
    createdAt: string;
}
```

### 2. Game Action Components

#### Delete Game Modal
```tsx
<Dialog open={showDeleteModal}>
    <h3>Delete Game</h3>
    <p>Are you sure you want to delete this game?</p>
    <TextField
        label="Reason"
        value={deleteReason}
        onChange={(e) => setDeleteReason(e.target.value)}
        required
    />
    <Button onClick={handleDelete}>Delete</Button>
    <Button onClick={() => setShowDeleteModal(false)}>Cancel</Button>
</Dialog>
```

#### Unapprove Match Modal
```tsx
<Dialog open={showUnapproveModal}>
    <h3>Unapprove Match</h3>
    <p>This will remove approval from the match.</p>
    <TextField
        label="Reason"
        value={unapproveReason}
        onChange={(e) => setUnapproveReason(e.target.value)}
        required
    />
    <Button onClick={handleUnapprove}>Unapprove</Button>
    <Button onClick={() => setShowUnapproveModal(false)}>Cancel</Button>
</Dialog>
```

### 3. Audit Log Viewer Component
```tsx
function AuditLogViewer({ targetId, targetType }: { targetId: number; targetType: string }) {
    const [logs, setLogs] = useState<AuditLogEntry[]>([]);
    
    // Fetch logs for the specific target
    useEffect(() => {
        const fetchLogs = async () => {
            const response = await apiClient.get(`/admin/audit-logs/${targetId}`);
            setLogs(response.data);
        };
        fetchLogs();
    }, [targetId]);

    return (
        <div>
            <h4>Change History</h4>
            {logs.map(log => (
                <div key={log.id} className="audit-log-entry">
                    <p>
                        <strong>{log.actionType}</strong> by {log.adminUsername}
                        <br />
                        <small>{new Date(log.createdAt).toLocaleString()}</small>
                    </p>
                    <p>Reason: {log.reason}</p>
                    <div className="state-diff">
                        {/* Show diff between previous and new state */}
                    </div>
                </div>
            ))}
        </div>
    );
}
```

## Implementation Steps

1. Database Changes
   - Create migration for audit log table
   - Add new columns to games and matches tables
   - Add necessary indexes

2. Backend Implementation
   - Create AdminAuditService
   - Implement game management endpoints
   - Add audit logging to existing admin actions
   - Add audit log retrieval endpoints

3. Frontend Implementation
   - Create AdminGameManagementPage
   - Add game action modals
   - Implement audit log viewer
   - Update navigation for new admin pages

4. Testing
   - Test all admin actions
   - Verify audit log creation
   - Test state restoration
   - Test UI components

## Security Considerations

1. Admin Action Validation
   - Verify admin status on every action
   - Validate action permissions
   - Prevent circular state changes

2. Audit Log Security
   - Ensure logs cannot be modified
   - Restrict access to admin users only
   - Sanitize sensitive data in logs

3. State Management
   - Maintain data integrity during state changes
   - Handle concurrent admin actions
   - Prevent race conditions

## Future Enhancements

1. Enhanced Audit Features
   - Export audit logs
   - Advanced filtering and search
   - Automated alerts for certain actions

2. Additional Admin Actions
   - Modify game details
   - Manage registrations
   - Handle edge cases

3. UI Improvements
   - Real-time updates
   - Better state visualization
   - Bulk actions interface