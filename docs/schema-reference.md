# SIC-JS v3.0 Schema Reference

This document provides a field-by-field reference for the SIC-JS v3.0 JSON Schema. The authoritative source is `packages/core/schema/sic-js-schema-v3.0.json`.

## Top-Level Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `sic_version` | string | Yes | Protocol version. Must be "2.0" or "3.0". | `"3.0"` |
| `round` | integer | Yes | Monotonically increasing round counter (≥ 1). | `5` |
| `entity` | object | Yes | The AGI entity producing this record. | See below |
| `state` | object | Yes | Current cognitive state snapshot. | See below |
| `relation` | object | Yes | Relationship context. | See below |
| `event` | object | Yes | What triggered this record. | See below |
| `intent` | object | Yes | Semantic intent layer. | See below |
| `task` | object | No (v3.0) | Task primitive (ought layer). Required if `sic_version` is "3.0". | See below |

## Entity Object

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `entity.name` | string | Yes | Name of the AGI entity. | `"德德"` |
| `entity.model` | string | No | Model identifier. | `"Claude Sonnet 4.6"` |

## State Object

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `state.context` | string | Yes | Current context summary. | `"Working on SIC-JS repo"` |
| `state.current_action` | string/null | Yes | What the entity is currently doing. Null triggers `semantic_rupture` WARN. | `"Writing code"` |
| `state.pending` | array | No | List of pending items. | `["Review spec"]` |

## Relation Object

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `relation.user` | string | Yes | The human user in this session. | `"安安"` |

## Event Object

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `event.timestamp` | string | Yes | ISO 8601 timestamp. | `"2026-06-01T08:00:00Z"` |
| `event.description` | string | Yes | What happened. | `"Task completed"` |
| `event.trigger` | string | No | What triggered this event. | `"user_request"` |

## Intent Object

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `intent.user_intent` | string | Yes | What the user wants. | `"Build a repo"` |
| `intent.system_intent` | string | Yes | What the system plans to do. | `"Creating repository"` |
| `intent.core_question` | string | No | The key question to resolve. | `"Is this complete?"` |

## Task Object (v3.0 only)

| Field | Type | Required | Constraint | Description | Example |
|-------|------|----------|-----------|-------------|---------|
| `task.id` | string | Yes | `[FROZEN]` Pattern: `^[A-Z]{1,2}-[1-9][0-9]{0,2}$` or with prefix | Unique, immutable task identifier. | `"A-1"` |
| `task.title` | string | Yes | — | Human-readable task title. | `"Build SIC-JS repo"` |
| `task.deliverable` | string | Yes | Non-empty | What constitutes completion. | `"Repo with all tests passing"` |
| `task.status` | string | Yes | `[FROZEN]` Enum: `{pending, in_progress, completed, dismissed, archived}` | Current task status. | `"in_progress"` |
| `task.created_round` | integer | Yes | `[FROZEN]` Must be ≤ `round` | Round when task was created. | `1` |
| `task.owner` | string | No | — | Who owns this task. | `"咩咩"` |
| `task.priority` | string | No | — | Priority level. | `"P0"` |
| `task.time_horizon` | string | No | — | Expected completion timeframe. | `"this session"` |

## Frozen Constraints

The following constraints are marked `[FROZEN]` and cannot be changed in any future version:

1. **task.id** — Once assigned, never changes. Used as stable DOM key for O(1) rendering.
2. **task.status** — Only the five enumerated values are valid. No extensions allowed.
3. **task.created_round** — Immutable after creation. Must always be ≤ current `round`.

## Validation Rules (Cross-field)

1. If `sic_version` is "3.0", `task` object is required.
2. If `sic_version` is "2.0", `task` object must NOT be present.
3. `task.created_round` must be ≤ `round`.
4. `task.status` must be one of the five valid values.
5. `task.deliverable` must be a non-empty string.
