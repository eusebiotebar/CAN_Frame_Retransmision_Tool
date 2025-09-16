---
docType: Software Requirements Verification Plan Report (SRVPR)
docSubtitle: CAN Frame Retransmission Tool
docVersion: 0.9.0
docAuthor: E. Tébar
createdDate: 2025-09-16
---

# Test Report - SRVP Functional Requirements

This document summarizes the latest test run and the verification status of the SRVP functional requirements.

## Summary

- Tests: 22 passed, 0 failed, 0 skipped (total 22)
- Requirements: 12 verified, 0 failed, 26 pending (total 38)

## Requirements Status

| Requirement | Status | Tests |
| --- | --- | --- |
| REQ-FUNC-INT-001 | \[x] Verified | tests/test_gui_logic.py::test_channel_detection_signal |
| REQ-FUNC-INT-002 | \[x] Verified | tests/test_gui_logic.py::test_two_distinct_selectors_for_channels |
| REQ-FUNC-INT-003 | \[x] Verified | tests/test_gui_logic.py::test_same_channel_selection_is_prevented |
| REQ-FUNC-INT-004 | [ ] Not Started |  |
| REQ-FUNC-INT-005 | \[x] Verified | tests/test_gui_logic.py::test_default_bitrate_is_250 |
| REQ-FUNC-INT-006 | [ ] Not Started |  |
| REQ-FUNC-INT-007 | [ ] Not Started |  |
| REQ-FUNC-INT-008 | [ ] Not Started |  |
| REQ-FUNC-INT-009 | \[x] Verified | tests/test_gui_logic.py::test_status_indicator_changes |
| REQ-FUNC-INT-010 | \[x] Verified | tests/test_gui_logic.py::test_latest_frames_view_exists |
| REQ-FUNC-LOG-001 | \[x] Verified | tests/test_can_logic.py::test_worker_handles_bus_creation_error |
| REQ-FUNC-LOG-002 | [ ] Not Started |  |
| REQ-FUNC-LOG-003 | \[x] Verified | tests/test_can_logic.py::test_signals_are_emitted_for_frames |
| REQ-FUNC-LOG-004 | \[x] Verified | tests/test_can_logic.py::test_can_frame_is_rewritten_and_retransmitted, tests/test_can_logic.py::test_can_frame_is_passed_through_when_no_rule_matches |
| REQ-FUNC-LOG-005 | \[x] Verified | tests/test_can_logic.py::test_can_frame_is_rewritten_and_retransmitted, tests/test_can_logic.py::test_can_frame_is_passed_through_when_no_rule_matches |
| REQ-FUNC-LOG-006 | \[x] Verified | tests/test_can_logic.py::test_retransmission_stops_when_worker_is_stopped |
| REQ-FUNC-LOG-007 | \[x] Verified | tests/test_can_logic.py::test_worker_handles_bus_creation_error |
| REQ-FUNC-LOG-008 | [ ] Not Started |  |
| REQ-FUNC-LOG-009 | [ ] Not Started |  |
| REQ-FUNC-LOG-010 | [ ] Not Started |  |
| REQ-FUNC-LOG-011 | [ ] Not Started |  |
| REQ-NFR-MNT-001 | [ ] Not Started |  |
| REQ-NFR-MNT-002 | [ ] Not Started |  |
| REQ-NFR-POR-001 | [ ] Not Started |  |
| REQ-NFR-POR-002 | [ ] Not Started |  |
| REQ-NFR-POR-003 | [ ] Not Started |  |
| REQ-NFR-POR-004 | [ ] Not Started |  |
| REQ-NFR-REL-001 | [ ] Not Started |  |
| REQ-NFR-REL-002 | [ ] Not Started |  |
| REQ-NFR-REL-003 | [ ] Not Started |  |
| REQ-NFR-REL-005 | [ ] Not Started |  |
| REQ-NFR-REL-006 | [ ] Not Started |  |
| REQ-NFR-SAF-001 | [ ] Not Started |  |
| REQ-NFR-SAF-002 | [ ] Not Started |  |
| REQ-NFR-USA-001 | [ ] Not Started |  |
| REQ-NFR-USA-002 | [ ] Not Started |  |
| REQ-NFR-USA-003 | [ ] Not Started |  |
| REQ-NFR-USA-004 | [ ] Not Started |  |

## Details

### REQ-FUNC-INT-001

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_gui_logic.py::test_channel_detection_signal` — passed

### REQ-FUNC-INT-002

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_gui_logic.py::test_two_distinct_selectors_for_channels` — passed

### REQ-FUNC-INT-003

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_gui_logic.py::test_same_channel_selection_is_prevented` — passed

### REQ-FUNC-INT-004

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-FUNC-INT-005

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_gui_logic.py::test_default_bitrate_is_250` — passed

### REQ-FUNC-INT-006

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-FUNC-INT-007

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-FUNC-INT-008

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-FUNC-INT-009

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_gui_logic.py::test_status_indicator_changes` — passed

### REQ-FUNC-INT-010

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_gui_logic.py::test_latest_frames_view_exists` — passed

### REQ-FUNC-LOG-001

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_can_logic.py::test_worker_handles_bus_creation_error` — passed

### REQ-FUNC-LOG-002

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-FUNC-LOG-003

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_can_logic.py::test_signals_are_emitted_for_frames` — passed

### REQ-FUNC-LOG-004

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_can_logic.py::test_can_frame_is_rewritten_and_retransmitted` — passed
  - ✅ `tests/test_can_logic.py::test_can_frame_is_passed_through_when_no_rule_matches` — passed

### REQ-FUNC-LOG-005

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_can_logic.py::test_can_frame_is_rewritten_and_retransmitted` — passed
  - ✅ `tests/test_can_logic.py::test_can_frame_is_passed_through_when_no_rule_matches` — passed

### REQ-FUNC-LOG-006

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_can_logic.py::test_retransmission_stops_when_worker_is_stopped` — passed

### REQ-FUNC-LOG-007

- Status: \[x] Verified
- Tests:
  - ✅ `tests/test_can_logic.py::test_worker_handles_bus_creation_error` — passed

### REQ-FUNC-LOG-008

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-FUNC-LOG-009

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-FUNC-LOG-010

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-FUNC-LOG-011

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-MNT-001

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-MNT-002

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-POR-001

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-POR-002

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-POR-003

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-POR-004

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-REL-001

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-REL-002

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-REL-003

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-REL-005

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-REL-006

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-SAF-001

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-SAF-002

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-USA-001

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-USA-002

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-USA-003

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet

### REQ-NFR-USA-004

- Status: [ ] Not Started
- Tests:
  - ➖ No tests mapped yet
