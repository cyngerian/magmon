# Game Deletion Implementation Plan

## Current Project State Analysis

### Backend Components
1. Models
   - User: Handles authentication and admin privileges
   - Game: Manages game sessions and their states
   - Match: Tracks game results and approvals
   - Deck: Manages player decks and versions

2. API Routes
   - Admin routes for user management
   - Game management routes
   - Match submission and approval routes

3. Database
   - PostgreSQL with migration support
   - Existing tables for core functionality

### Frontend Components
1. Admin Interface
   - User management page
   - Password reset functionality
   - Admin-only route protection

2. Game Management
   - Game listing and filtering
   - Match submission interface
   - Basic game state management

## Implementation Plan

### 1. Database Changes

#### Create Admin Audit Log Table
```sql
CREATE TABLE admin_audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id INTEGER NOT NULL,
    previous_state JSONB,
    new_state JSONB,
    reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_admin_audit_target ON admin_audit_logs(target_type, target_id);
CREATE INDEX idx_admin_audit_admin ON admin_audit_logs(admin_id);
```

#### Update Games Table
```sql
ALTER TABLE games 
    ADD COLUMN deleted_at TIMESTAMP,
    ADD COLUMN deleted_by_id INTEGER REFERENCES users(id),
    ADD COLUMN last_admin_action VARCHAR(50),
    ADD COLUMN last_admin_action_at TIMESTAMP;
```

### 2. Backend Implementation

#### Create Migration
- Create new migration file for database changes
- Include both audit log table creation and games table updates

#### Implement AdminAuditService
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

#### Add Admin Game Management Endpoints
```python
@bp.route('/admin/games/<int:game_id>', methods=['DELETE'])
@admin_required
def delete_game(game_id):
    """Soft delete a game and all related data"""

@bp.route('/admin/games/<int:game_id>/restore', methods=['POST'])
@admin_required
def restore_game(game_id):
    """Restore a soft-deleted game"""
```

### 3. Frontend Implementation

#### Create AdminGameManagementPage Component
```typescript
interface AdminGameAction {
    gameId: number;
    action: 'delete' | 'restore';
    reason: string;
}

function AdminGameManagementPage() {
    // Implementation details...
}
```

#### Create Game Action Modals
- DeleteGameModal for confirming game deletion
- RestoreGameModal for confirming game restoration
- Audit log viewer component

#### Update Navigation
- Add new admin game management route
- Update admin navigation menu

### 4. Testing Plan

1. Database Testing
   - Verify audit log creation
   - Test soft delete functionality
   - Check database constraints and indexes

2. Backend Testing
   - Test admin endpoints
   - Verify audit logging
   - Test error handling

3. Frontend Testing
   - Test admin interface functionality
   - Verify modal interactions
   - Check audit log display

## Implementation Steps

1. Database Changes
   - Create migration for audit log table
   - Add soft delete columns to games table
   - Add necessary indexes

2. Backend Implementation
   - Create AdminAuditService
   - Implement game management endpoints
   - Add audit logging to existing admin actions

3. Frontend Implementation
   - Create AdminGameManagementPage
   - Add game action modals
   - Implement audit log viewer

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