# LineFlex Development Roadmap

## Phase 0 — Repository foundation
- [x] Create public repository
- [x] Add README, product brief, research plan and roadmap

## Phase 1 — Research and scope
- [ ] Verify competitor capabilities
- [ ] Gather dated industry evidence
- [ ] Select one initial manufacturing workflow
- [ ] Define sample data and user roles
- [ ] Freeze MVP requirements

## Phase 2 — Factory Capability Registry
- [x] Create SQLite factory and capability tables
- [x] Register and retrieve factory records
- [x] Record machines, processes, materials and certifications
- [x] Search factories by name, city and state
- [x] Edit factory details and capabilities
- [x] Delete factories and associated capabilities
- [x] Add validation for required fields and capacity
- [x] Add factory-level data-source and review-status metadata API (user-entered labels, not independent verification)
- [ ] Define requirement, candidate and qualification entities

## Phase 3 — Core manufacturing workflow
- [ ] Add requirement entry
- [ ] Compare requirements with capability records
- [ ] Show matched, mismatched and unknown fields
- [ ] Add second-source qualification checklist
- [ ] Add owners, dates and evidence references

## Phase 4 — Backend, quality and usability
- [x] Build FastAPI backend
- [x] Add factory CRUD API endpoints
- [x] Add API and database tests
- [x] Add input validation and error handling
- [x] Document local setup and API usage
- [x] Pin direct dependencies
- [x] Verify 17 automated tests pass
- [ ] Review deprecation warning from test client
- [ ] Capture genuine application screenshots
- [ ] Expand edge-case testing

**Current test result:** 17 passed, 0 failed, with one non-failing deprecation warning.

## Phase 5 — Deployment and evaluation
- [ ] Review security and data-handling requirements
- [ ] Decide whether deployment is appropriate
- [ ] Deploy only with non-sensitive demo data
- [ ] Collect structured user feedback
- [ ] Reassess product scope and commercial assumptions

## Important limitation

LineFlex currently stores user-entered manufacturing information. It does not verify actual capacity, technical compatibility, supplier suitability or customer approval.

Update this roadmap only when a feature has been implemented and tested.
