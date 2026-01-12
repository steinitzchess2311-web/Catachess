# Optimistic Locking

This document describes the optimistic locking mechanism used to handle concurrent edits in the Workspace system.

## Overview

**Optimistic locking** allows multiple users to read the same resource simultaneously, but prevents conflicting concurrent writes. Instead of locking resources pessimistically, we assume conflicts are rare and detect them when they occur.

## Why Optimistic Locking?

### The Problem

In a collaborative editing environment:

1. User A loads a study (version 5)
2. User B loads the same study (version 5)
3. User A makes changes and saves (version becomes 6)
4. User B makes changes and tries to save
5. **Without locking**: User B's changes would overwrite User A's changes (lost update)

### The Solution

Optimistic locking uses **version numbers** (or ETags) to detect conflicts:

1. User A loads study with version 5
2. User B loads study with version 5
3. User A saves with version 5 → Success, version becomes 6
4. User B tries to save with version 5 → **Conflict detected** (current version is 6)
5. System returns 409 Conflict with the latest version
6. User B can now merge or reload

## Implementation

### Version Field

Every mutable resource has a `version` field:

```python
# In tables/studies.py (example)
class Study(Base):
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # ... other fields
```

### Version Increment

Every write operation increments the version:

```python
# In domain/services/study_service.py
async def update_study(self, command: UpdateStudyCommand) -> Study:
    study = await self.repo.get_by_id(command.study_id)

    # Check version match
    if study.version != command.version:
        raise OptimisticLockError(
            f"Version conflict: expected {command.version}, "
            f"got {study.version}"
        )

    # Update fields
    study.title = command.title
    study.version += 1  # Increment version

    await self.repo.update(study)
    return study
```

### API Endpoints

#### Using If-Match Header

The standard HTTP approach uses the `If-Match` header with ETag:

```http
PUT /studies/abc123
If-Match: "5"
Content-Type: application/json

{
  "title": "Updated Study Title"
}
```

**Response on Success (200 OK):**
```http
HTTP/1.1 200 OK
ETag: "6"
Content-Type: application/json

{
  "id": "abc123",
  "title": "Updated Study Title",
  "version": 6
}
```

**Response on Conflict (409 Conflict):**
```http
HTTP/1.1 409 Conflict
ETag: "6"
Content-Type: application/json

{
  "error": "Version conflict",
  "message": "Resource has been modified by another user",
  "current_version": 6,
  "your_version": 5,
  "current_data": {
    "id": "abc123",
    "title": "Study Title Modified by User A",
    "version": 6
  }
}
```

#### Using Request Body Version

Alternatively, include version in the request body:

```http
PUT /studies/abc123
Content-Type: application/json

{
  "title": "Updated Study Title",
  "version": 5
}
```

### Frontend Implementation

#### Basic Pattern

```typescript
async function updateStudy(studyId: string, updates: StudyUpdate) {
  // Load current version
  const study = await api.getStudy(studyId);

  try {
    // Send update with version
    const result = await api.updateStudy(studyId, {
      ...updates,
      version: study.version
    });

    return result;
  } catch (error) {
    if (error.status === 409) {
      // Conflict detected
      return handleConflict(error.current_data, updates);
    }
    throw error;
  }
}
```

#### Conflict Resolution Strategies

**1. Ask User (Recommended)**

```typescript
async function handleConflict(
  serverData: Study,
  localChanges: StudyUpdate
): Promise<Study> {
  // Show conflict dialog
  const choice = await showConflictDialog({
    serverVersion: serverData,
    localChanges: localChanges,
    options: ['keep_server', 'use_local', 'merge']
  });

  switch (choice) {
    case 'keep_server':
      return serverData;

    case 'use_local':
      // Force update with new version
      return api.updateStudy(serverData.id, {
        ...localChanges,
        version: serverData.version
      });

    case 'merge':
      // Implement custom merge logic
      return mergeChanges(serverData, localChanges);
  }
}
```

**2. Automatic Retry**

For non-conflicting fields:

```typescript
async function updateStudyWithRetry(
  studyId: string,
  updates: StudyUpdate,
  maxRetries: number = 3
): Promise<Study> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const study = await api.getStudy(studyId);
      return await api.updateStudy(studyId, {
        ...updates,
        version: study.version
      });
    } catch (error) {
      if (error.status === 409 && i < maxRetries - 1) {
        // Retry with fresh version
        continue;
      }
      throw error;
    }
  }
}
```

**3. Last-Write-Wins (Not Recommended)**

```typescript
// ⚠️ Use with caution - can lose data
async function forceUpdate(studyId: string, updates: StudyUpdate) {
  const study = await api.getStudy(studyId);
  return api.updateStudy(studyId, {
    ...updates,
    version: study.version  // Always use latest version
  });
}
```

## Endpoints with Optimistic Locking

All mutation endpoints that modify collaborative content support optimistic locking:

### Study Operations

| Endpoint | Method | Version Required |
|----------|--------|------------------|
| `/studies/{id}` | PUT | Yes |
| `/studies/{id}/chapters/{cid}/moves` | POST | Yes |
| `/studies/{id}/chapters/{cid}/variations` | POST | Yes |
| `/studies/{id}/chapters/{cid}/moves/{path}/annotations` | POST | Yes |

### Discussion Operations

| Endpoint | Method | Version Required |
|----------|--------|------------------|
| `/discussions/{id}` | PUT | Yes |
| `/replies/{id}` | PUT | Yes |

### Chapter Operations

| Endpoint | Method | Version Required |
|----------|--------|------------------|
| `/studies/{id}/chapters/{cid}` | PUT | Yes |
| `/studies/{id}/chapters/{cid}/reorder` | POST | Yes |

## Testing

### Unit Tests

```python
# tests/test_optimistic_locking.py

async def test_concurrent_update_conflict():
    """Test that concurrent updates are detected."""
    study = await service.create_study(...)

    # Both users load version 1
    user_a_version = study.version  # 1
    user_b_version = study.version  # 1

    # User A updates successfully
    await service.update_study(UpdateStudyCommand(
        study_id=study.id,
        version=user_a_version,
        title="User A's changes"
    ))

    # User B's update should fail
    with pytest.raises(OptimisticLockError):
        await service.update_study(UpdateStudyCommand(
            study_id=study.id,
            version=user_b_version,  # Stale version!
            title="User B's changes"
        ))
```

### API Integration Tests

```python
# tests/test_api_optimistic_locking.py

async def test_api_returns_409_on_conflict():
    """Test that API returns 409 on version conflict."""
    # Create study
    response = await client.post("/studies", json={"title": "Test"})
    study = response.json()

    # Update with correct version
    response = await client.put(
        f"/studies/{study['id']}",
        json={"title": "Update 1", "version": study["version"]}
    )
    assert response.status_code == 200

    # Try to update with stale version
    response = await client.put(
        f"/studies/{study['id']}",
        json={"title": "Update 2", "version": study["version"]}  # Stale!
    )
    assert response.status_code == 409
    assert "current_version" in response.json()
    assert "current_data" in response.json()
```

## Best Practices

### 1. Always Include Version

```python
# ✅ DO: Include version in all updates
command = UpdateStudyCommand(
    study_id=study_id,
    version=current_version,
    title=new_title
)
```

### 2. Handle 409 Gracefully

```python
# ✅ DO: Catch and handle conflicts
try:
    result = await update_study(command)
except OptimisticLockError as e:
    # Show user-friendly error
    raise HTTPException(
        status_code=409,
        detail={
            "error": "Conflict",
            "message": "Resource has been modified",
            "current_version": e.current_version,
            "current_data": e.current_data
        }
    )
```

### 3. Return Current Data on Conflict

```python
# ✅ DO: Include current data in 409 response
except OptimisticLockError:
    current_study = await repo.get_by_id(study_id)
    raise HTTPException(
        status_code=409,
        detail={
            "current_version": current_study.version,
            "current_data": StudyResponse.model_validate(current_study)
        }
    )
```

### 4. Increment Version on Every Write

```python
# ✅ DO: Increment version for all mutations
study.title = new_title
study.version += 1

# ❌ DON'T: Forget to increment
study.title = new_title  # Version not incremented!
```

### 5. Use Atomic Updates

```python
# ✅ DO: Update version atomically with data
result = await session.execute(
    update(Study)
    .where(Study.id == study_id, Study.version == old_version)
    .values(title=new_title, version=old_version + 1)
)

if result.rowcount == 0:
    raise OptimisticLockError()
```

## Common Pitfalls

### 1. Not Checking Version

```python
# ❌ DON'T: Skip version check
async def update_study(study_id: str, title: str):
    study = await repo.get_by_id(study_id)
    study.title = title  # No version check!
    await repo.update(study)
```

### 2. Using Server Timestamp Instead

```python
# ❌ DON'T: Use timestamps for conflict detection
if study.updated_at != expected_timestamp:
    raise ConflictError()
# Timestamps can be identical for concurrent requests!
```

### 3. Ignoring 409 Errors

```typescript
// ❌ DON'T: Ignore conflicts
try {
  await api.updateStudy(id, changes);
} catch (error) {
  console.log('Update failed');  // User loses changes!
}
```

## Performance Considerations

- **Version checks are fast**: Simple integer comparison
- **No database locks**: No blocking, high concurrency
- **Minimal overhead**: One extra integer field per row
- **Scales well**: Works in distributed systems

## Related Documentation

- [Event System](./event_system.md)
- [Concurrency Policy](../domain/policies/concurrency.py)
- [API Endpoints](./api_reference.md)
