# LineFlex Development Roadmap

## Phase 0 — Repository foundation
- [x] Create public repository
- [x] Add README, product brief, research plan, and roadmap

## Phase 1 — Research and scope
- [ ] Verify competitor capabilities
- [ ] Gather dated industry evidence
- [ ] Select and validate one initial manufacturing workflow
- [ ] Define sample data and user roles
- [ ] Freeze MVP requirements

## Phase 2 — Factory Capability Registry
- [x] Create SQLite factory and capability tables
- [x] Register, retrieve, search, edit, and delete factory records
- [x] Record machines, processes, materials, and certifications
- [x] Add validation for required fields and stated capacity
- [x] Add factory-level data-source and review-status metadata API
- [ ] Add verified document upload and controlled evidence handling

## Phase 3 — Production requirement and capability comparison
- [x] Create production requirement records with part number, demand, unit, and notes
- [x] Store required machine, process, material, and certification labels
- [x] Compare requirements against registered factory capability labels
- [x] Report matches, partial gaps, unrecorded categories, and capacity-unit/capacity shortfalls
- [x] Expose requirement creation, listing, retrieval, deletion, and comparison API endpoints
- [x] Add Streamlit requirement-entry and comparison screens
- [x] Add requirement editing and version history
- [x] Add candidate shortlist and human decision/approval capture

**Current comparison rule:** Exact case-insensitive label matching, plus comparison of user-entered stated monthly capacity when units match. No fuzzy matching or engineering approval is inferred.

## Phase 4 — Quality and usability
- [x] Build FastAPI backend and factory CRUD endpoints
- [x] Add factory provenance/review metadata endpoints
- [x] Add input validation and error handling
- [x] Add automated tests for factory CRUD, provenance, requirement storage, matching outcomes, and APIs
- [x] Document local setup and API usage
- [ ] Review the existing test-client deprecation warning
- [ ] Capture genuine application screenshots
- [ ] Expand edge-case and usability testing

**Exit condition:** Local demo can be reproduced using synthetic data, all tests pass, and the limitations of capability matching are clear.

## Phase 5 — Qualification and second-source workflow
- [x] Start a qualification by linking a production requirement to an alternative factory
- [x] Create a standard second-source review checklist
- [x] Track check status, owner, due date, evidence reference, and notes
- [x] Move completed checklists to Ready for review
- [x] Record human decisions with rationale and decision history
- [x] Expose qualification, checklist, decision, and history API endpoints
- [x] Add Streamlit qualification workspace
- [ ] Add notifications and reminders
- [ ] Add role-based approval permissions and authenticated reviewer identity
- [ ] Add reusable checklist templates by industry or part type

## Phase 6 — Security, deployment, and evaluation
- [ ] Review security and data-handling requirements
- [ ] Add authentication, roles, and access controls
- [ ] Decide whether deployment is appropriate
- [ ] Deploy only with non-sensitive demo data
- [ ] Collect structured user feedback
- [ ] Reassess product scope and commercial assumptions

## Important limitations

LineFlex stores user-entered manufacturing information. Capability matching is a preliminary screen based on exact text labels. It does not verify free capacity, technical compatibility, quality, certification validity, supplier suitability, or customer approval. A potential match is not an approval to transfer production.

Update this roadmap only when a capability has been implemented and tested.
