# LineFlex Development Roadmap

This roadmap tracks implemented, partially implemented, and planned work. A checkbox is marked complete only when the capability is present and has been checked.

## Phase 0 — Repository foundation
- [x] Create public repository
- [x] Add initial README
- [x] Add product brief
- [x] Add research plan
- [x] Add development roadmap

## Phase 1 — Research and scope
- [ ] Verify competitor capabilities
- [ ] Gather dated industry evidence
- [ ] Select one initial manufacturing workflow
- [ ] Define sample data and user roles
- [ ] Freeze MVP requirements

**Exit condition:** A narrow use case is supported by credible evidence and is not simply a duplicate of an existing product.

## Phase 2 — Data model and prototype
- [x] Create initial SQLite tables for factories and capability values
- [x] Store factory name, location, stated monthly capacity, and capacity unit
- [x] Store machine, process, material, and certification entries
- [x] Register and list factory capability records in the local Streamlit app
- [x] Search records by factory name, city, or state
- [ ] Edit and delete factory records
- [ ] Add data provenance and verification labels
- [ ] Define requirement, candidate, and qualification entities

**Current result:** A local Factory Capability Registry works with user-entered/demo information. It is not yet a supplier qualification or production-transfer system.

## Phase 3 — Core workflow
- [ ] Add requirement entry
- [ ] Compare requirements with capability records
- [ ] Show matched, mismatched, and unknown fields
- [ ] Add second-source qualification checklist
- [ ] Add owners, dates, and evidence references

**Exit condition:** The prototype demonstrates one complete workflow using synthetic data without claiming automatic technical approval.

## Phase 4 — Quality and usability
- [x] Add initial database tests for record creation/retrieval, city search, and basic validation
- [x] Add pinned direct dependencies and local run instructions
- [ ] Expand tests for duplicate entries, malformed data, and other edge cases
- [ ] Improve validation and error handling
- [ ] Document limitations and setup steps in full
- [ ] Capture and store genuine application screenshots

**Current test baseline:** Four database tests passed in the local run for the initial registry milestone.

**Exit condition:** The documented local demo can be reproduced by another developer and its limitations are clear.

## Phase 5 — Deployment and evaluation
- [ ] Review security and data-handling requirements
- [ ] Decide whether deployment is appropriate
- [ ] Deploy only with non-sensitive demo data
- [ ] Collect structured feedback
- [ ] Reassess product scope and commercial assumptions

## Progress tracking

Update this file only when a milestone is actually completed and can be demonstrated in the repository.
