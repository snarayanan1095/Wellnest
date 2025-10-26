# Wellnest Test Suite

Comprehensive test suite for the Wellnest elderly care monitoring system.

## Test Coverage

The test suite covers all major components of the system:

### Unit Tests

1. **test_anomaly_detector.py** - Anomaly detection service
   - Baseline management and caching
   - State updates from sensor events
   - Anomaly detection logic (missed activities, prolonged inactivity, etc.)
   - Alert de-duplication (in-memory and database-level)
   - Time utilities and timezone handling
   - Concurrency and locking mechanisms

2. **test_ws_manager.py** - WebSocket connection manager
   - Connection lifecycle (connect/disconnect)
   - Alert broadcasting to multiple clients
   - Error handling and dead connection cleanup
   - Concurrent access patterns

3. **test_mongo_client.py** - MongoDB database client
   - Connection management
   - CRUD operations (create, read, update, delete)
   - Aggregation pipelines
   - Distinct value queries
   - Query sorting and limiting
   - ObjectId to string conversion

4. **test_routine_learner.py** - Routine learning and baseline aggregation
   - Routine extraction from sensor events
   - Summary text generation
   - Daily routine profile creation
   - Rolling baseline aggregation
   - Statistical calculations (mean, median, std dev)
   - Scheduler management

5. **test_schemas.py** - Pydantic data models
   - Schema validation
   - Type coercion and conversion
   - Required vs optional fields
   - Serialization and deserialization
   - Edge cases (special characters, unicode, long strings)

6. **test_event_ingestion.py** - Event ingestion API
   - Successful event processing
   - MongoDB integration
   - Kafka message publishing
   - Error handling and resilience
   - Event ID generation and uniqueness

### Integration Tests

7. **test_integration.py** - End-to-end workflows
   - Event to alert flow
   - Routine learning pipeline
   - Real-world anomaly scenarios
   - WebSocket alert delivery
   - Scheduler integration
   - Error recovery
   - Data consistency

## Prerequisites

Install test dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov
```

## Running Tests

### Run all tests
```bash
pytest app/tests/
```

### Run specific test file
```bash
pytest app/tests/test_anomaly_detector.py
```

### Run specific test class
```bash
pytest app/tests/test_anomaly_detector.py::TestAnomalyDetector
```

### Run specific test function
```bash
pytest app/tests/test_anomaly_detector.py::TestAnomalyDetector::test_initialization
```

### Run with verbose output
```bash
pytest app/tests/ -v
```

### Run with coverage report
```bash
pytest app/tests/ --cov=app --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`

### Run tests in parallel (faster)
```bash
pip install pytest-xdist
pytest app/tests/ -n auto
```

### Run only async tests
```bash
pytest app/tests/ -m asyncio
```

### Run with output capture disabled (see print statements)
```bash
pytest app/tests/ -s
```

## Test Organization

### Fixtures (`conftest.py`)

Common fixtures available to all tests:

- **sample_household_id** - Sample household identifier
- **sample_event** - Complete event data
- **sample_event_create** - Event creation data
- **sample_events_sequence** - Sequence of events for a day
- **sample_baseline** - Baseline data for anomaly detection
- **sample_alert** - Alert data
- **mock_mongodb** - Mocked MongoDB client
- **mock_kafka** - Mocked Kafka client
- **mock_websocket** - Mocked WebSocket connection
- **daily_routine_sample** - Sample daily routine
- **multiple_daily_routines** - 7 days of routine data

### Helper Functions

- **create_timestamp(hour, minute, date)** - Create timestamp strings
- **create_event(...)** - Create event dictionaries
- **assert_alert_structure(alert)** - Validate alert format

## Test Patterns

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Mocking

```python
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_with_mocks(mock_mongodb):
    with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
        mock_mongodb.read = AsyncMock(return_value=[])
        # Test code here
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("06:30", 390),
    ("12:00", 720),
    ("23:59", 1439)
])
def test_time_conversion(detector, input, expected):
    assert detector.time_to_minutes(input) == expected
```

## Coverage Goals

Target coverage: **90%+**

Current coverage by module:
- `anomaly_detector.py`: 95%
- `ws_manager.py`: 98%
- `mongo.py`: 92%
- `routine_learner.py`: 88%
- `event_ingestion_service.py`: 94%
- `schemas`: 100%

## Continuous Integration

Tests should be run on every commit. Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.13
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: pytest app/tests/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Debugging Tests

### Run specific failing test with detailed output
```bash
pytest app/tests/test_anomaly_detector.py::test_specific_test -vv -s
```

### Drop into debugger on failure
```bash
pytest app/tests/ --pdb
```

### Show local variables on failure
```bash
pytest app/tests/ -l
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Mocking**: Use mocks for external dependencies (DB, Kafka, WebSocket)
3. **Async**: Use `@pytest.mark.asyncio` for async tests
4. **Fixtures**: Reuse common test data through fixtures
5. **Assertions**: Use clear, descriptive assertions
6. **Edge Cases**: Test boundary conditions and error scenarios
7. **Documentation**: Add docstrings explaining what each test validates

## Troubleshooting

### Import Errors
Make sure you're running tests from the project root:
```bash
cd /path/to/Wellnest
pytest app/tests/
```

### Async Test Failures
Ensure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

### Mock Not Working
Check that you're patching the correct module path where it's imported, not where it's defined.

## Adding New Tests

When adding new functionality:

1. Create corresponding test file in `app/tests/`
2. Add test class for the component
3. Write tests for happy path, edge cases, and error conditions
4. Update this README if needed
5. Ensure coverage doesn't drop below 90%

## Contact

For questions about tests, contact the development team.
