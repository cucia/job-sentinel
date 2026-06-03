# Queue Metadata Preservation Failure Audit

**Date:** 2026-06-03T18:46:38Z  
**Issue:** workflow_type, execution_strategy, workflow_confidence, workflow_indicators lost during enqueue → dequeue cycle

---

## Root Cause: Task Model Fields Not Persisted

### The Problem

**Task Model defines workflow fields (lines 47-50):**
```python
# backend/runtime/task_model.py line 47-50
workflow_type: Optional[str] = None
execution_strategy: Optional[str] = None
workflow_confidence: float = 0.0
workflow_indicators: dict = field(default_factory=dict)
```

**Database schema does NOT include these columns (lines 29-48):**
```sql
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    source_platform TEXT NOT NULL,
    status TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    worker_id TEXT,
    result TEXT,
    error_message TEXT,
    manual_review_context TEXT,
    metadata TEXT,              ← Only generic metadata column
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
    -- ❌ NO workflow_type column
    -- ❌ NO execution_strategy column
    -- ❌ NO workflow_confidence column
    -- ❌ NO workflow_indicators column
)
```

### Serialization

**Task.to_dict() includes workflow fields (lines 52-64):**
```python
def to_dict(self) -> dict:
    """Convert task to dictionary, serializing enums and datetimes."""
    data = asdict(self)
    # ... handles status, result, dates
    # ✅ workflow_type is in data (from asdict)
    # ✅ execution_strategy is in data (from asdict)
    # ✅ workflow_confidence is in data (from asdict)
    # ✅ workflow_indicators is in data (from asdict)
    return data
```

### Storage - Save

**TaskStorage.save_task() only saves metadata column (line 129):**
```python
json.dumps(task.metadata),  # ← Only metadata column saved
# ❌ workflow_type not saved
# ❌ execution_strategy not saved
# ❌ workflow_confidence not saved
# ❌ workflow_indicators not saved
```

**What happens:**
```
Task object with:
  workflow_type = "linkedin_easy_apply"
  execution_strategy = "linkedin_easy_apply_flow"
  workflow_confidence = 0.95
  metadata = {"job": {...}}
  
→ save_task() called
  ├─ Only saves metadata to metadata column
  ├─ workflow_type field ignored
  ├─ execution_strategy field ignored
  ├─ workflow_confidence field ignored
  └─ workflow_indicators field ignored
  
→ Database row contains:
  metadata = '{"job": {...}}'  ← Only job data
  (no workflow fields)
```

### Storage - Retrieve

**TaskStorage._row_to_task() reconstructs from row (lines 413-434):**
```python
def _row_to_task(row: tuple) -> Task:
    return Task(
        task_id=row[0],
        ...
        metadata=json.loads(row[11]) if row[11] else {},  # Line 429
        ...
    )
    # ❌ workflow_type not in row - defaults to None
    # ❌ execution_strategy not in row - defaults to None
    # ❌ workflow_confidence not in row - defaults to 0.0
    # ❌ workflow_indicators not in row - defaults to {}
```

**What happens:**
```
Database row contains:
  metadata = '{"job": {...}}'
  (no workflow columns)
  
→ _row_to_task() called
  ├─ Reads metadata column → {"job": {...}}
  ├─ workflow_type not in row → None
  ├─ execution_strategy not in row → None
  ├─ workflow_confidence not in row → 0.0
  └─ workflow_indicators not in row → {}
  
→ Reconstructed Task object has:
  workflow_type = None  ❌ LOST
  execution_strategy = None  ❌ LOST
  workflow_confidence = 0.0  ❌ LOST
  workflow_indicators = {}  ❌ LOST
```

---

## Data Flow Trace

### Before Enqueue
```
Task(
    task_id="task_001",
    workflow_type="linkedin_easy_apply",
    execution_strategy="linkedin_easy_apply_flow",
    workflow_confidence=0.95,
    workflow_indicators={...},
    metadata={"job": {...}}
)
```

### After enqueue()
```
Queue.enqueue(task)
  └─ storage.save_task(task)  ← Line 29 in queue.py
      └─ TaskStorage.save_task() (line 87)
          └─ INSERT/UPDATE with parameters (line 117-134)
              ├─ Saves: metadata = json.dumps(task.metadata)
              ├─ Ignores: workflow_type
              ├─ Ignores: execution_strategy
              ├─ Ignores: workflow_confidence
              └─ Ignores: workflow_indicators
```

### After dequeue()
```
Queue.dequeue(limit=1)
  └─ storage.get_queued_tasks() (line 41 in queue.py)
      └─ TaskStorage.get_queued_tasks() (line 159)
          └─ SELECT * FROM tasks WHERE status = QUEUED
              └─ TaskStorage._row_to_task(row) (line 177)
                  └─ Reconstructs Task from row
                      ├─ workflow_type = None (not in database)
                      ├─ execution_strategy = None (not in database)
                      ├─ workflow_confidence = 0.0 (not in database)
                      └─ workflow_indicators = {} (not in database)
```

### Result
```
Retrieved Task(
    task_id="task_001",
    workflow_type=None,  ❌ LOST
    execution_strategy=None,  ❌ LOST
    workflow_confidence=0.0,  ❌ LOST
    workflow_indicators={},  ❌ LOST
    metadata={"job": {...}}
)
```

---

## Minimal Fix: Two Options

### Option A: Store in metadata dict (non-breaking)

**Change:** Add workflow fields to metadata before saving

**Location:** TaskStorage.save_task() before line 129

```python
def save_task(self, task: Task) -> None:
    import json
    
    # Preserve workflow fields in metadata
    metadata_to_save = dict(task.metadata)
    metadata_to_save.update({
        "_workflow_type": task.workflow_type,
        "_execution_strategy": task.execution_strategy,
        "_workflow_confidence": task.workflow_confidence,
        "_workflow_indicators": task.workflow_indicators,
    })
    
    with self._connect() as conn:
        conn.execute(
            """INSERT INTO tasks (...) VALUES (...)""",
            (
                ...
                json.dumps(metadata_to_save),  # Include workflow fields
                ...
            ),
        )
```

**In _row_to_task():**
```python
def _row_to_task(row: tuple) -> Task:
    import json
    
    metadata = json.loads(row[11]) if row[11] else {}
    
    # Extract workflow fields from metadata
    workflow_type = metadata.pop("_workflow_type", None)
    execution_strategy = metadata.pop("_execution_strategy", None)
    workflow_confidence = metadata.pop("_workflow_confidence", 0.0)
    workflow_indicators = metadata.pop("_workflow_indicators", {})
    
    return Task(
        ...
        metadata=metadata,
        workflow_type=workflow_type,
        execution_strategy=execution_strategy,
        workflow_confidence=workflow_confidence,
        workflow_indicators=workflow_indicators,
    )
```

**Pros:**
- No schema change
- No migration needed
- Backward compatible

**Cons:**
- Workflow data mixed in metadata
- Not properly structured

### Option B: Add database columns (proper design)

**Change:** Add columns to tasks table schema

**Location:** TaskStorage._init_schema() lines 29-50

```python
def _init_schema(self) -> None:
    with self._connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                source_platform TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                worker_id TEXT,
                result TEXT,
                error_message TEXT,
                manual_review_context TEXT,
                metadata TEXT,
                workflow_type TEXT,           ← ADD THIS
                execution_strategy TEXT,      ← ADD THIS
                workflow_confidence REAL,     ← ADD THIS
                workflow_indicators TEXT,     ← ADD THIS
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT
            )
            """
        )
```

**Update save_task() (lines 99-134):**
```python
conn.execute(
    """
    INSERT INTO tasks (
        task_id, job_id, source_platform, status, priority, retry_count,
        max_retries, worker_id, result, error_message, manual_review_context,
        metadata, workflow_type, execution_strategy, workflow_confidence,
        workflow_indicators, created_at, updated_at, started_at, completed_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(task_id) DO UPDATE SET
        ...
        workflow_type = excluded.workflow_type,
        execution_strategy = excluded.execution_strategy,
        workflow_confidence = excluded.workflow_confidence,
        workflow_indicators = excluded.workflow_indicators,
    """,
    (
        ...
        json.dumps(task.metadata),
        task.workflow_type,
        task.execution_strategy,
        task.workflow_confidence,
        json.dumps(task.workflow_indicators),
        ...
    ),
)
```

**Update _row_to_task() (lines 413-434):**
```python
def _row_to_task(row: tuple) -> Task:
    import json
    
    return Task(
        task_id=row[0],
        ...
        metadata=json.loads(row[11]) if row[11] else {},
        workflow_type=row[12],
        execution_strategy=row[13],
        workflow_confidence=row[14] if row[14] else 0.0,
        workflow_indicators=json.loads(row[15]) if row[15] else {},
        ...
    )
```

**Pros:**
- Proper schema design
- Workflow data properly separated
- Efficient queries

**Cons:**
- Requires schema migration for existing databases
- Breaking change for deployed systems

---

## Recommendation

**Use Option A (store in metadata)** for minimal fix:

1. ✅ No schema changes
2. ✅ No migrations
3. ✅ Backward compatible
4. ✅ Workflow data preserved
5. ❌ Not ideal design (mixing concerns)

**Then migrate to Option B later** for proper design.

---

## Files to Modify

**File 1:** `backend/persistence/task_storage.py`

**Change 1 - save_task() around line 129:**
```python
# Before:
json.dumps(task.metadata),

# After:
metadata_to_save = dict(task.metadata or {})
metadata_to_save.update({
    "_workflow_type": task.workflow_type,
    "_execution_strategy": task.execution_strategy,
    "_workflow_confidence": task.workflow_confidence,
    "_workflow_indicators": task.workflow_indicators,
})
json.dumps(metadata_to_save),
```

**Change 2 - _row_to_task() around line 429:**
```python
# Before:
metadata=json.loads(row[11]) if row[11] else {},

# After:
metadata=self._extract_metadata_and_workflow(row[11])[0],
workflow_type=self._extract_metadata_and_workflow(row[11])[1],
execution_strategy=self._extract_metadata_and_workflow(row[11])[2],
workflow_confidence=self._extract_metadata_and_workflow(row[11])[3],
workflow_indicators=self._extract_metadata_and_workflow(row[11])[4],
```

**Add helper method:**
```python
@staticmethod
def _extract_metadata_and_workflow(metadata_json):
    """Extract metadata and workflow fields from stored JSON."""
    import json
    
    metadata = json.loads(metadata_json) if metadata_json else {}
    
    workflow_type = metadata.pop("_workflow_type", None)
    execution_strategy = metadata.pop("_execution_strategy", None)
    workflow_confidence = metadata.pop("_workflow_confidence", 0.0)
    workflow_indicators = metadata.pop("_workflow_indicators", {})
    
    return (metadata, workflow_type, execution_strategy, workflow_confidence, workflow_indicators)
```

---

## Validation After Fix

### Test 1: Metadata Preserved Through Queue

```python
task = Task(
    task_id="test_1",
    workflow_type="indeed",
    execution_strategy="generic_form_flow",
    workflow_confidence=0.85,
    metadata={"job": {"title": "Engineer"}},
)

queue.enqueue(task)
retrieved = queue.peek()

assert retrieved.workflow_type == "indeed"
assert retrieved.execution_strategy == "generic_form_flow"
assert retrieved.workflow_confidence == 0.85
assert retrieved.metadata == {"job": {"title": "Engineer"}}
```

### Test 2: Round-trip Through Storage

```python
task.workflow_indicators = {"key": "value"}

storage.save_task(task)
retrieved = storage.get_task(task.task_id)

assert retrieved.workflow_type == task.workflow_type
assert retrieved.execution_strategy == task.execution_strategy
assert retrieved.workflow_confidence == task.workflow_confidence
assert retrieved.workflow_indicators == task.workflow_indicators
```

---

## Conclusion

**Root Cause:** Workflow fields are defined in Task model but not persisted to database. Only generic `metadata` column is saved.

**Result:** After enqueue → dequeue, workflow_type and related fields are lost (set to None/0/empty).

**Fix:** Add workflow fields to metadata dict before saving, extract them after loading.

**Files Changed:** 1 (`backend/persistence/task_storage.py`)

**Breaking Changes:** None

**Backward Compatibility:** Preserved

