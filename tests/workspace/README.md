# Workspace Module Tests

This directory contains all tests for the workspace module.

## Test Structure

```
tests/workspace/
├── unit/              # Unit tests (models, policies, utilities)
├── integration/       # Integration tests (repos, services)
├── api/               # API endpoint tests
└── e2e/               # End-to-end tests (full workflows)
```

## Running Tests

### All workspace tests
```bash
pytest tests/workspace/
```

### Specific test categories
```bash
pytest tests/workspace/unit/          # Unit tests only
pytest tests/workspace/integration/   # Integration tests only
pytest tests/workspace/api/           # API tests only
```

### With coverage
```bash
pytest tests/workspace/ --cov=backend/modules/workspace --cov-report=html
```

## Test Organization

### Unit Tests (`unit/`)
- `test_types.py` - Core type enums and validators
- `test_permissions.py` - Permission policy logic
- `test_limits.py` - System limits and constraints
- `test_domain_models.py` - Domain model behavior

### Integration Tests (`integration/`)
- `test_node_repo.py` - Node repository operations
- `test_acl_repo.py` - ACL repository operations
- `test_event_repo.py` - Event repository operations
- `test_node_service.py` - Node service business logic
- `test_share_service.py` - Share service business logic
- `test_event_bus.py` - Event publishing and subscription

### API Tests (`api/`)
- `test_nodes_api.py` - Node CRUD endpoints
- `test_shares_api.py` - Share and permission endpoints
- `test_auth.py` - Authentication and authorization
- `test_errors.py` - Error handling and status codes

### E2E Tests (`e2e/`)
- `test_create_workspace_flow.py` - Full workspace creation
- `test_share_collaborate_flow.py` - Sharing and collaboration
- `test_tree_operations_flow.py` - Complex tree operations

## Test Fixtures

Common fixtures are defined in `conftest.py`:
- `engine` - Test database engine
- `session` - Test database session
- `node_repo` - Node repository
- `acl_repo` - ACL repository
- `event_repo` - Event repository
- `node_service` - Node service
- `share_service` - Share service

## Coverage Goals

- Overall: > 80%
- Critical paths: 100%
- Domain logic: > 90%
- API endpoints: > 85%

## Writing New Tests

1. **Choose the right category**: Unit, integration, API, or E2E
2. **Use fixtures**: Leverage existing fixtures for setup
3. **Test behavior, not implementation**: Focus on outcomes
4. **Test edge cases**: Boundary conditions, errors, concurrency
5. **Keep tests isolated**: Each test should be independent
6. **Use descriptive names**: Test name should explain what it tests

Example:
```python
@pytest.mark.asyncio
async def test_create_nested_folder_structure(node_service):
    \"\"\"Test creating deeply nested folder structure (3+ levels).\"\"\"
    # Test implementation
```

## Phase 1 Test Coverage

Phase 1 includes comprehensive tests for:
- ✅ Node CRUD operations
- ✅ Permission checking
- ✅ Tree operations (move, path updates)
- ✅ Share operations
- ✅ Share links
- ✅ API endpoints
- ✅ Error handling

Total test files: 7
Total test cases: 50+
Coverage: > 85%
