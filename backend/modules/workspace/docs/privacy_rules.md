# Privacy Control Rules

This document details the privacy control mechanisms in the Workspace system.

## Visibility Levels

The system supports three visibility levels for nodes (workspace/folder/study):

### PRIVATE

- **Who can see**: Only the owner
- **Behavior**:
  - Node is invisible in search results for non-owners
  - Direct URL access returns 404 (not 403) for non-owners
  - Shared-with-me lists do not include private nodes
  - Children inherit PRIVATE status unless explicitly shared

### SHARED

- **Who can see**: Owner + explicitly granted users
- **Behavior**:
  - Only appears in search results for owner and users with permissions
  - Direct URL access returns 404 for users without permissions
  - Appears in "Shared with me" for granted users
  - Children can have different permissions

### PUBLIC

- **Who can see**: Everyone
- **Behavior**:
  - Appears in public search results
  - Direct URL access allowed for all users
  - Can be indexed by external systems
  - Children can be more restrictive

## 404 vs 403 Strategy

**Important**: The system uses **404 instead of 403** for unauthorized access to prevent information leakage.

### Rationale

- **403 (Forbidden)**: Reveals that the resource exists, but the user doesn't have access
- **404 (Not Found)**: Hides the existence of the resource entirely

### Implementation

```python
# ❌ DON'T: Reveals existence
if not has_permission(user, resource):
    raise HTTPException(status_code=403)

# ✅ DO: Hides existence
resource = get_resource_if_accessible(user, resource_id)
if not resource:
    raise HTTPException(status_code=404)
```

### When to use 403

Use 403 only when:
1. User is authenticated and viewing their own resources
2. User has some permission but attempting a forbidden action
3. Example: Editor trying to delete (needs admin permission)

## Discussion System Permission Inheritance

Discussions **inherit permissions from their target object** (study/folder/workspace).

### Permission Requirements

| Action | Required Permission |
|--------|-------------------|
| View discussion | `viewer` on target object |
| Create thread | `commenter` on target object |
| Reply to thread | `commenter` on target object |
| Edit own reply | `commenter` on target object |
| Edit any reply | `editor` on target object |
| Delete own reply | `commenter` on target object |
| Delete any reply | `admin` on target object |
| Pin/resolve thread | `editor` on target object |

### Inheritance Rules

1. **Automatic Inheritance**: Discussion permissions automatically follow target object ACL
2. **No Separate ACL**: Discussions do not have their own ACL table
3. **Cascading Changes**: Changing object permissions immediately affects all discussions
4. **404 for Inaccessible**: If user can't access target object, discussions return 404

### Example

```python
# User has 'viewer' permission on study-123
# ✅ Can view discussions on study-123
# ❌ Cannot create thread (needs 'commenter')
# ❌ Cannot edit any replies (needs 'editor')
```

## Search Result Filtering

Search results are automatically filtered based on user permissions.

### Implementation

```python
async def search(user_id: str, query: str) -> list[SearchResult]:
    # Get all matching results
    all_results = await search_index.search(query)

    # Filter by permissions
    accessible_results = [
        result for result in all_results
        if can_read(user_id, result.target_id)
    ]

    return accessible_results
```

### Search Index Privacy

- **Indexed**: All content is indexed for fast search
- **Filtered**: Results are filtered at query time
- **No Leakage**: Private content never appears in results for unauthorized users

## API Endpoint Patterns

### Correct Pattern

```python
@router.get("/studies/{study_id}")
async def get_study(
    study_id: str,
    user_id: str = Depends(get_current_user_id),
    repo: StudyRepository = Depends(get_study_repo),
    acl_repo: ACLRepository = Depends(get_acl_repo),
):
    # Check permission first
    if not await can_read(acl_repo, study_id, user_id):
        # Return 404, not 403
        raise HTTPException(status_code=404, detail="Study not found")

    study = await repo.get_by_id(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    return StudyResponse.model_validate(study)
```

### Anti-Pattern

```python
# ❌ DON'T: Separate existence check reveals information
study = await repo.get_by_id(study_id)
if not study:
    raise HTTPException(status_code=404)

if not await can_read(acl_repo, study_id, user_id):
    raise HTTPException(status_code=403)  # Information leakage!
```

## Move Annotations vs Discussions

The system has a **dual-layer comment model**:

### Move Annotations (Professional Layer)

- **Permission**: Requires `editor` permission
- **Purpose**: Professional chess analysis
- **Export**: Exported with PGN
- **Privacy**: Follows study privacy settings

### Discussions (Collaboration Layer)

- **Permission**: Requires `commenter` permission
- **Purpose**: User collaboration and questions
- **Export**: NOT exported with PGN
- **Privacy**: Inherits from target object

This separation ensures professional annotations remain clean while allowing casual collaboration.

## Testing Privacy Rules

All API endpoints must have tests covering:

1. ✅ Unauthorized access returns 404
2. ✅ Search results exclude unauthorized content
3. ✅ Direct URL access respects permissions
4. ✅ Discussion permissions follow target object
5. ✅ Permission changes cascade correctly

See `tests/test_privacy_rules.py` for comprehensive test coverage.

## Best Practices

1. **Always check permissions first** before querying database
2. **Use 404 for unauthorized access** to hide resource existence
3. **Filter search results** at query time based on permissions
4. **Test permission boundaries** for all API endpoints
5. **Document permission requirements** in API schemas

## Related Documentation

- [ACL System](./acl_system.md)
- [Discussion System](./discussion_system.md)
- [Search Architecture](./search_indexing.md)
