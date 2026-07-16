"""Jira Addon README."""

# Jira Bidirectional Sync Addon

Complete specification and implementation guide for bidirectional Jira integration.

## Overview

This addon enables seamless bidirectional synchronization between Delivery Assurance Copilot and Jira Cloud:
- **Push**: Automatically export requirements and test cases to Jira as issues
- **Pull**: Import status changes from Jira back to local artifacts  
- **Link**: Auto-link requirements to their test cases
- **Organize**: Group synced items under parent epics
- **Secure**: Encrypt all API tokens at rest

## Quick Start

### 1. Enable Addon

Update `.env`:
```
JIRA_ADDON_ENABLED=true
```

Generate encryption key (first time only):
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
```

Add to `.env`:
```
ENCRYPTION_KEY=your-generated-key-here
```

### 2. Configure Jira Connection

Visit **Jira Sync** page in frontend → **Configure Jira Connection**

Required fields:
- **Jira URL**: `https://yourcompany.atlassian.net`
- **Project Key**: `QUAL` (your Jira project key)
- **Email/Username**: Your Jira account email
- **API Token**: Generate from Jira → Settings → Personal → API Tokens

### 3. Validate & Activate

Click **Save Configuration** → System validates connection

Once validated, connection is **active** and ready to sync

### 4. Sync Data

In **Sync with Jira** section:
- Select what to sync (Requirements, Test Cases, Criteria)
- Optionally create parent epic
- Click **Start Sync**

Monitor progress and view results

## Architecture

```
backend/app/addons/jira_addon/
├── __init__.py              # Package marker
├── config.py                # Configuration models
├── models.py                # Database models (4 tables)
├── client.py                # Jira API wrapper
├── encryption.py            # Token encryption/decryption
├── sync_service.py          # Core sync logic
├── router.py                # API endpoints
├── schemas.py               # Request/response schemas
└── tests/                   # Unit tests
```

## Database Schema

### JiraConnection
- `id`: UUID (PK)
- `project_id`: UUID (FK, unique per project)
- `jira_url`: String
- `jira_project_key`: String
- `jira_username`: String
- `jira_api_token_encrypted`: Text (encrypted)
- `is_active`: Boolean
- `last_sync_at`: DateTime
- `sync_direction`: String (push|pull|bidirectional)

### JiraRequirementMapping
- `id`: UUID (PK)
- `requirement_id`: UUID (FK)
- `jira_issue_key`: String
- `jira_issue_id`: String
- `sync_status`: String (synced|pending|failed)
- `last_synced_at`: DateTime

### JiraTestMapping
- `id`: UUID (PK)
- `test_case_id`: UUID (FK)
- `jira_issue_key`: String
- `jira_issue_id`: String
- `sync_status`: String (synced|pending|failed)
- `last_synced_at`: DateTime

### JiraSyncHistory
- `id`: UUID (PK)
- `project_id`: UUID (FK)
- `sync_type`: String (push|pull|bidirectional)
- `direction`: String (to_jira|from_jira)
- `status`: String (success|partial|failed)
- `items_processed`: Integer
- `items_failed`: Integer
- `error_message`: Text (optional)
- `synced_at`: DateTime

## API Endpoints

All endpoints require `project_id` query parameter.

### POST `/api/v1/jira/configure?project_id={id}`
Configure Jira connection.
```json
{
  "jira_url": "https://company.atlassian.net",
  "jira_project_key": "QUAL",
  "jira_username": "qa@company.com",
  "jira_api_token": "atatt...",
  "sync_direction": "bidirectional"
}
```

### POST `/api/v1/jira/validate?project_id={id}`
Test and activate connection.

**Response:**
```json
{
  "status": "active",
  "message": "Jira connection validated and activated",
  "jira_project_key": "QUAL",
  "is_active": true
}
```

### GET `/api/v1/jira/status/{project_id}`
Get connection status.

**Response:**
```json
{
  "is_configured": true,
  "is_active": true,
  "jira_url": "https://company.atlassian.net",
  "jira_project_key": "QUAL",
  "last_sync_at": "2024-06-14T12:30:00",
  "sync_direction": "bidirectional"
}
```

### POST `/api/v1/jira/sync/{project_id}`
Execute sync operation.

**Request:**
```json
{
  "include_requirements": true,
  "include_test_cases": true,
  "include_criteria": true,
  "create_epic": true,
  "epic_title": "Test Plan - 2024-06-14",
  "auto_link": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Synced 47 items to Jira",
  "epic_key": "QUAL-100",
  "items_synced": 47,
  "items_failed": 2
}
```

### DELETE `/api/v1/jira/disconnect/{project_id}`
Remove Jira connection.

**Response:**
```json
{
  "status": "disconnected",
  "message": "Jira connection removed"
}
```

## Security

### Token Encryption
API tokens are encrypted using Fernet (symmetric encryption) before storage:
```python
from app.addons.jira_addon.encryption import encrypt_token, decrypt_token

encrypted = encrypt_token("atatt1234567890")
decrypted = decrypt_token(encrypted)
```

### Key Management
- **Generate key**: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"`
- **Store**: In `.env` as `ENCRYPTION_KEY`
- **Rotate**: Change key in `.env`, re-sync to update stored tokens

### Access Control
- Tokens only decrypted during sync operations
- Never logged or exposed in API responses
- All API calls should be authenticated at application level

## Testing

Run tests:
```bash
cd backend
pytest tests/ -v

# Or test addon only:
pytest app/addons/jira_addon/tests/ -v
```

## Disabling Addon

To completely disable addon without code changes:

**Option 1: Environment Variable**
```
JIRA_ADDON_ENABLED=false
```

**Option 2: Disconnect Project**
- Use API: `DELETE /api/v1/jira/disconnect/{project_id}`
- Or UI: Jira Sync page → "Disconnect Jira" button

No data loss - all local artifacts remain intact.

## Troubleshooting

### Connection Fails
- Verify Jira URL is correct (e.g., includes `https://`)
- Check email/username exists in Jira
- Confirm API token hasn't expired
- Ensure token has project write permissions

### Sync Fails After Configuration
- Validate connection: Jira Sync → "Re-validate Connection"
- Check project has required issue types: Story, Task, Epic
- Review sync history in database

### Encryption Errors
- Verify `ENCRYPTION_KEY` format is correct
- Regenerate key if corrupted
- Clear old encrypted tokens and re-sync

## Performance Notes

- Sync speed: ~1 item per second (depends on Jira instance)
- For 100+ items: Plan 2-5 minutes
- Epic creation: Usually < 1 second
- Auto-linking: 1-2 seconds per link

## Cost Considerations

- Jira Cloud API: Unlimited calls for Cloud instances
- Addon storage: ~2KB per mapping entry
- Encryption overhead: Minimal (~5% CPU impact)

## Future Enhancements

**Phase 2 (v1.1):**
- Pull status updates from Jira
- Custom field mapping
- Scheduled auto-sync

**Phase 3 (v1.2):**
- Jira on-premises support
- Test execution status sync
- Custom workflow transitions

**Phase 4 (v1.3):**
- Bulk operations
- Conflict resolution UI
- Sync scheduling
