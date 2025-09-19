---
docType: Software Requirements Verification Plan (SRVP)
docSubtitle: CAN Frame Retransmission Tool
docVersion: 1.2.0
docAuthor: E. Tébar
createdDate: 2025-09-04
lastModifiedDate: 2025-09-17
---

# CAN Frame Retransmission Tool (SRVP)

---

## Purpose

This document defines the plan, methods, and criteria for verifying the requirements specified in [`/1/`](#referenced-documents). It ensures that each requirement is testable and provides a framework for tracking verification status.

## Referenced Documents

[DOC-001]: (SRS.md)
[DOC-002]: (SRVP_TR.md)

|Ref. No. |Doc. Number |Version    |Title                                                |
|:--------|:-----------|:----------|:----------------------------------------------------|
| /1/     | ATID-10201 | Latest    | [(SRS) for CAN Frame Retransmission Tool][DOC-001]                           |
| /2/     | ATID-10301_TR | Latest    | [(SRVP_TR) Test Report for SRVP][DOC-002]                           |

## Definitions

### Abbreviations

| Abbreviation | Definition                              |
| :----------- | :-------------------------------------- |
| **AC**       | Acceptance Criteria                     |
| **CAN**      | Controller Area Network                 |
| **GUI**      | Graphical User Interface                |
| **ID**       | Identifier                              |
| **SRS**      | Software Requirements Specification     |
| **SRVP**     | Software Requirements Verification Plan |
| **TBD**      | To Be Determined                        |

### Terms

| Term                | Definition                                                                                                           |
| :------------------ | :------------------------------------------------------------------------------------------------------------------- |
| **Inspection**      | A static review of documents, code, or design artifacts.                                                             |
| **Analysis**        | Evaluation of requirements or design through modeling, calculation, or simulation.                                   |
| **Test**            | Dynamic execution of the software with specific inputs to observe outputs and behavior.                              |
| **Demonstration**   | Showing the functionality of the software to stakeholders without formal test cases.                                 |
| **Status**          | The current state of verification for a requirement (e.g., "\[ ] Not Started", "In Progress", "Verified", "Failed"). |

## Verification Overview

Verification will be an ongoing process throughout the software development lifecycle, primarily focused on the testing phase. Each requirement from the SRS will be traced to one or more verification methods. The verification status of each requirement will be tracked.

## Test Levels and Strategy

Verification will be conducted at the following levels:

- **Analysis:** Verification by static code review, inspection of documentation, or review of tool-generated outputs (e.g., memory maps).
- **Unit Test:** Testing of individual software functions or modules in isolation to ensure they perform as designed.
- **Integration Test:** Testing of combined software modules to expose faults in their interaction. This includes testing protocol stacks with hardware interfaces.
- **System Test:** End-to-end testing of the fully integrated system to evaluate its compliance with the specified requirements. Performance and reliability tests are conducted at this level.

## Verification Matrix

### Functional Requirements Verification

| ID | Verification Method | Acceptance Criteria | Status |
| :--- | :--- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----- |
| REQ-FUNC-INT-001 | Test | Upon application startup, a dropdown or list box is populated with unique identifiers for all detected Kvaser CAN channels. If no devices are found, a clear message indicating this is displayed. | \[ ] Not Started |
| REQ-FUNC-INT-002 | Test | The GUI presents two distinct selection mechanisms (e.g., dropdowns) for "Input Channel" and "Output Channel". | \[ ] Not Started |
| REQ-FUNC-INT-003 | Test | If the user attempts to select the same channel for both input and output, an error message is displayed (e.g., "Input and Output channels cannot be the same"), and the selection is prevented or reset. | \[ ] Not Started |
| REQ-FUNC-INT-004 | Test | The GUI provides input fields or dropdowns for "Input Bitrate" and "Output Bitrate." | \[ ] Not Started |
| REQ-FUNC-INT-005 | Test | Upon application startup or channel selection, the bitrate input fields are pre-populated with "250 kbps". | \[ ] Not Started |
| REQ-FUNC-INT-006 | Test | A GUI component (e.g., a table) is provided where users can enter pairs of "Original CAN ID" and "Rewritten CAN ID." The table supports adding, editing, and deleting entries. | \[ ] Not Started |
| REQ-FUNC-INT-007 | Test | If an invalid ID format is entered, an error message is displayed, and the entry is highlighted or rejected until corrected. | \[ ] Not Started |
| REQ-FUNC-INT-008 | Test | A clearly labeled button exists. Its text and behavior change contextually (e.g., "Start" when stopped, "Stop" when running). | \[ ] Not Started |
| REQ-FUNC-INT-009 | Test | A dedicated GUI element (e.g., a label, LED icon) changes its text/color to reflect "Stopped", "Listening", "Receiving", or "Error" states. | \[ ] Not Started |
| REQ-FUNC-INT-010 | Test | A scrollable table or list view is present, showing the latest N (e.g., 100) received frames. Each row includes Timestamp, Direction (Input/Output), CAN ID, DLC, and Data. | \[ ] Not Started |
| REQ-FUNC-INT-011 | Test | A File menu is present with Import and Export menu items. Clicking Import opens a file dialog for loading mapping files. Clicking Export opens a file dialog for saving mapping files. | \[ ] Not Started |
| REQ-FUNC-INT-012 | Test | A Settings menu is present with options to open the settings dialog, save settings to file, and load settings from file. | \[ ] Not Started |
| REQ-FUNC-INT-013 | Test | When importing a CSV file with header lines, the header lines are automatically detected and skipped, and only valid data rows are imported into the mapping table. | \[ ] Not Started |
| REQ-FUNC-INT-014 | Test | When exporting mapping data to CSV, the file includes a header line with column descriptions (e.g., "Original ID,Rewritten ID"). | \[ ] Not Started |
| REQ-FUNC-INT-015 | Test | A Settings dialog can be opened with three tabs: Connection, Logging, and Advanced Throttling. Each tab contains the appropriate configuration controls. | \[ ] Not Started |
| REQ-FUNC-INT-016 | Test | Settings can be saved to a JSON file and successfully loaded from that file, preserving all configuration values across application sessions. | \[ ] Not Started |
| REQ-FUNC-LOG-001 | Test | When the "Start" button is pressed, the status indicator changes to "Listening". The `python-can` Kvaser backend successfully opens both specified channels with their respective bitrates. If an error occurs during opening, the status transitions to "Error" and an appropriate message is displayed. | \[ ] Not Started |
| REQ-FUNC-LOG-002 | Test | The input channel continuously polls or uses callbacks to detect incoming CAN frames. No frames are missed during normal operation within the buffer capacity. | \[ ] Not Started |
| REQ-FUNC-LOG-003 | Test | When a frame is received, it appears in the "Latest Frames" table/list within 100ms. The entry includes the precise timestamp, "Input" direction, original CAN ID, DLC, and Data. The status indicator transitions from "Listening" to "Receiving". | \[ ] Not Started |
| REQ-FUNC-LOG-004 | Test | If the received CAN ID exists as an "Original CAN ID" in the mapping table, the frame's ID is changed to the corresponding "Rewritten CAN ID." If no mapping is found, the original CAN ID is retained. | \[ ] Not Started |
| REQ-FUNC-LOG-005 | Test | The modified (or original) CAN frame is sent via the output CAN channel. A corresponding entry appears in the "Latest Frames" table/list with the "Output" direction and the rewritten/original CAN ID within 100ms of reception. | \[ ] Not Started |
| REQ-FUNC-LOG-006 | Test | When the "Stop" button is pressed, no further frames are received or transmitted. Both `python-can` buses are closed successfully. The status indicator changes to "Stopped". | \[ ] Not Started |
| REQ-FUNC-LOG-007 | Test | If device detection fails, a clear error message is displayed, and the channel selection dropdowns remain empty or indicate "No Devices Found." If channel opening fails (e.g., busy, permissions), an error message is displayed, the status indicator shows "Error," and the retransmission process does not start. | \[ ] Not Started |
| REQ-FUNC-LOG-008 | Test | If `python-can` reports a bitrate error during channel opening or operation, an error message is displayed, the status indicator shows "Error," and the retransmission stops. | \[ ] Not Started |
| REQ-FUNC-LOG-009 | Test | If a bus-off event occurs on an active channel, a warning/error message is displayed, and the status indicator changes to "Error" or "Bus-Off". Retransmission is paused or stopped. | \[ ] Not Started |
| REQ-FUNC-LOG-010 | Test / Inspection | Verify that LogManager creates a new log file each session with a timestamped filename. | \[ ] Not Started |
| REQ-FUNC-LOG-011 | Test | Each log entry includes a timestamp with millisecond precision, direction (Input/Output), CAN ID, DLC, and Data in a human-readable format. | \[ ] Not Started |

### Non-functional Requirements Verification

| ID | Verification Method | Acceptance Criteria | Status |
| :--- | :--- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :----- |
| REQ-NFR-REL-001 | Test | When a bus-off condition is detected, the system attempts to re-open the affected channel. If successful, it resumes retransmission; otherwise, it marks the channel as permanently failed after N retries and indicates an "Error" status. The retry count is configurable. | \[ ] Not Started |
| REQ-NFR-REL-002 | Analysis / Test | Monitor memory usage using OS tools (e.g., Task Manager). After 24 hours of continuous operation with the specified load, the memory footprint remains below the threshold. | \[ ] Not Started |
| REQ-NFR-MNT-001 | Review / Inspection | Code and documentation are organized into modules with clear responsibilities; a short architecture diagram and module map exists. | \[ ] Not Started |
| REQ-NFR-SAF-001 | Inspection / Demo | The application displays an explicit disclaimer in the About/Startup screen and user documentation stating it is not for safety-critical control. | \[ ] Not Started |
| REQ-NFR-SAF-002 | Test / Inspection | A runtime warning is shown before enabling retransmission and in the mapping-edit dialogs; the warning text and acceptance are logged. | \[ ] Not Started |
| REQ-NFR-POR-001 | System Test | Installation and runtime on a Windows 11 VM succeeds; GUI and CAN backend function as expected. | \[ ] Not Started |
| REQ-NFR-POR-002 | Analysis / Test | The application runs under Python 3.10+ interpreter without syntax/runtime errors; dependencies are installable. | \[ ] Not Started |
| REQ-NFR-POR-003 | Integration Test | GUI components render correctly under PyQt6 in the target environment. | \[ ] Not Started |
| REQ-NFR-POR-004 | Integration Test | Integration test with Kvaser hardware and `python-can` Kvaser backend demonstrates send/receive functionality. | \[ ] Not Started |
| REQ-NFR-USA-001 | Performance / System Test | Under a sustained retransmission load, GUI responsiveness metrics (click latency, UI thread blocking) remain within acceptable bounds; no hangs observed. | \[ ] Not Started |
| REQ-NFR-USA-002 | Test | The timestamps in the UI include milliseconds and match logged timestamps within a small tolerance. | \[ ] Not Started |
| REQ-NFR-USA-003 | Usability / Demo | Usability testing with at least two users confirms add/edit/delete workflows complete without errors; context menus and validation are present. | \[ ] Not Started |
| REQ-NFR-USA-004 | Inspection / Test | A sample of common error conditions shows user-facing messages that include cause and suggested action. | \[ ] Not Started |

## Verification Methods

The following methods will be employed to verify the software requirements:

- **Inspection:** This involves a static review of design documents, source code, and configuration files. It is primarily used for requirements related to code structure, documentation, and explicit statements (e.g., disclaimers).
- **Analysis:** This method involves evaluating requirements through calculations, modeling, or simulations without necessarily executing the software in full. It is particularly useful for performance, resource usage, and complex logical requirements where direct testing might be impractical or require extensive setup.
- **Test:** This is the primary verification method, involving the dynamic execution of the software with predefined test cases, inputs, and expected outputs. This includes:
  - **Unit Tests:** Verify individual components or functions in isolation.
  - **Integration Tests:** Verify the interaction between different components or modules.
  - **System Tests:** Verify the complete, integrated system against the specified requirements in a simulated or real environment.
  - **User Acceptance Tests (UAT):** Involve end-users testing the application in a realistic scenario to ensure it meets their operational needs.
- **Demonstration:** This method involves showcasing the software's functionality to stakeholders, often in a less formal setting than a structured test. It is useful for verifying GUI elements, user workflow, and general usability aspects.

## Verification Schedule

Verification activities will be integrated into the agile development sprints. A high-level schedule is outlined below, with detailed sprint-specific test plans to be developed during iteration planning.

- **Sprint 1:**
  - Inspection of initial design documents and architecture (REQ-NFR-MNT-001).
  - Unit testing for core CAN communication logic (REQ-FUNC-LOG-001 , REQ-FUNC-LOG-002, REQ-FUNC-LOG-005).
  - Initial GUI component testing for channel selection and bitrate configuration (REQ-FUNC-INT-001, REQ-FUNC-INT-002, REQ-FUNC-INT-004, REQ-FUNC-INT-005).
- **Sprint 2:**
  - Integration testing for GUI-CAN communication.
  - System testing for basic retransmission functionality with ID mapping (REQ-FUNC-LOG-003, REQ-FUNC-LOG-004).
  - Testing of input validation (REQ-FUNC-INT-003, REQ-FUNC-INT-007).
- **Sprint 3:**
  - System testing for error handling scenarios (REQ-FUNC-LOG-007, REQ-FUNC-LOG-008, REQ-FUNC-LOG-009).
  - Testing of logging features (REQ-FUNC-LOG-010, REQ-FUNC-LOG-011).
  - Usability testing for GUI responsiveness and clarity (REQ-NFR-USA-001, REQ-NFR-USA-002, REQ-NFR-USA-003, REQ-NFR-USA-004).
- **Sprint 4:**
  - Stress testing for reliability and memory usage (REQ-NFR-REL-001, REQ-NFR-REL-002).
  - Final system-wide regression testing.
  - Formal Inspection of safety-related documentation and warnings (REQ-NFR-REL-005, REQ-NFR-REL-006).
  - User Acceptance Testing (UAT) with selected end-users.
- **Post-Release:**
  - Continuous monitoring and defect resolution.

## Verification Environment

The verification environment will consist of the following components:

- **Hardware:**
  - Windows 11 desktop computer(s) (Minimum 8GB RAM, Quad-core processor)
  - At least two Kvaser CAN interfaces (e.g., Kvaser Leaf Light V2, Kvaser USBcan Pro 2xHS) connected via USB.
  - A functional CAN bus network (e.g., two ECUs, or a CAN bus simulator) to connect the Kvaser devices for realistic frame transmission and reception.
  - Network analysis tools (e.g., Wireshark with CAN plugin, Kvaser CanKing) for independent verification of CAN bus traffic if needed.
- **Software:**
  - Windows 11 Operating System.
  - Python 3.10+ installed with `pip` for package management.
  - `python-can` library and its Kvaser backend dependencies.
  - PyQt6 library.
  - Official Kvaser device drivers installed.
  - IDE (e.g., VS Code, PyCharm) for development and debugging.
  - Version Control System (e.g., Git).
  - Testing Framework (e.g., `pytest` for unit/integration tests).
  - System monitoring tools (e.g., Windows Task Manager, Python `memory_profiler`) for NFR-002.
- **Documentation:**
  - Latest version of the SRS.
  - Latest version of the SRVP.
  