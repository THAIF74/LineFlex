"""Streamlit workspace for requirement candidate shortlists."""

import pandas as pd
import streamlit as st

from candidate_shortlists import (
    CANDIDATE_DECISIONS,
    FINAL_CANDIDATE_STATUSES,
    create_requirement_candidate,
    get_candidate,
    get_requirement_candidates,
    record_candidate_decision,
)
from database import get_factories
from planning import compare_requirement_to_factories, get_production_requirements


def render_candidate_shortlist_workspace():
    st.header("Candidate Shortlist")
    st.caption(
        "Compare registered factories for a production requirement and record a human shortlist decision. "
        "Selection is not supplier approval."
    )

    requirements = get_production_requirements()
    factories = get_factories()
    if not requirements:
        st.info("Create a production requirement before building a candidate shortlist.")
        return
    if not factories:
        st.info("Register at least one factory before building a candidate shortlist.")
        return

    requirement_labels = {
        item["id"]: f'{item["requirement_name"]} — {item["part_number"] or "No part number"} (ID {item["id"]})'
        for item in requirements
    }
    chosen_requirement_id = st.selectbox(
        "Production requirement",
        options=list(requirement_labels),
        format_func=lambda value: requirement_labels[value],
        key="candidate_requirement_id",
    )
    existing = get_requirement_candidates(chosen_requirement_id)
    existing_factory_ids = {item["factory_id"] for item in existing}
    available_factories = [item for item in factories if item["id"] not in existing_factory_ids]

    st.subheader("Add an alternative factory")
    if available_factories:
        factory_labels = {
            item["id"]: f'{item["factory_name"]} — {item["city"]}, {item["state"]} (ID {item["id"]})'
            for item in available_factories
        }
        with st.form("add_requirement_candidate", clear_on_submit=True):
            factory_id = st.selectbox(
                "Factory candidate",
                options=list(factory_labels),
                format_func=lambda value: factory_labels[value],
            )
            added_by = st.text_input("Added by (optional)", max_chars=120)
            notes = st.text_area("Shortlist notes (optional)", max_chars=1000)
            add_clicked = st.form_submit_button("Add to Shortlist", type="primary")
        if add_clicked:
            try:
                candidate_id = create_requirement_candidate(
                    chosen_requirement_id, factory_id, added_by=added_by, notes=notes
                )
                st.success(f"Factory added to shortlist. Candidate ID: {candidate_id}")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
    else:
        st.info("Every registered factory is already on this requirement's shortlist.")

    st.subheader("Shortlisted factories")
    existing = get_requirement_candidates(chosen_requirement_id)
    if not existing:
        st.info("No factories have been shortlisted for this requirement yet.")
        return

    comparison = compare_requirement_to_factories(chosen_requirement_id)
    comparison_by_factory = {
        item["factory_id"]: item["overall_status"] for item in comparison["results"]
    }
    st.dataframe(
        pd.DataFrame([
            {
                "Candidate ID": item["id"],
                "Factory": item["factory_name"],
                "Location": f'{item["city"]}, {item["state"]}',
                "Capability screen": comparison_by_factory.get(item["factory_id"], "No comparison"),
                "Shortlist status": item["status"],
                "Added by": item["added_by"] or "Not recorded",
            }
            for item in existing
        ]),
        width="stretch",
        hide_index=True,
    )

    candidate_labels = {
        item["id"]: f'{item["factory_name"]} — {item["status"]} (Candidate {item["id"]})'
        for item in existing
    }
    selected_id = st.selectbox(
        "Choose a candidate to review",
        options=list(candidate_labels),
        format_func=lambda value: candidate_labels[value],
        key="selected_candidate_id",
    )
    selected = get_candidate(selected_id)
    if selected is None:
        st.error("The selected candidate could not be found.")
        return

    st.markdown(f'### {selected["factory_name"]}')
    st.write(f'**Requirement:** {selected["requirement_name"]} ({selected["part_number"] or "No part number"})')
    st.write(f'**Factory location:** {selected["city"]}, {selected["state"]}')
    st.write(f'**Stated capacity:** {selected["monthly_capacity"]:,.2f} {selected["capacity_unit"]}')
    st.write(f'**Capability comparison:** {comparison_by_factory.get(selected["factory_id"], "No comparison result")}')
    if selected["notes"]:
        st.write(f'**Shortlist notes:** {selected["notes"]}')
    st.caption("Capability comparison uses entered labels and stated capacity only; it is not technical or quality approval.")

    if selected["status"] in FINAL_CANDIDATE_STATUSES:
        st.info("This candidate has a final shortlist decision. Its decision history is retained and locked.")
    else:
        st.subheader("Record a human decision")
        with st.form("candidate_decision_form"):
            decision = st.selectbox("Decision", options=list(CANDIDATE_DECISIONS))
            decision_by = st.text_input("Decision maker", max_chars=120)
            rationale = st.text_area("Reason for this decision", max_chars=1000)
            decision_clicked = st.form_submit_button("Save Decision", type="primary")
        if decision_clicked:
            try:
                record_candidate_decision(
                    selected_id, decision, decision_by=decision_by, rationale=rationale
                )
                st.success(f"Candidate decision recorded: {decision}")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

    if selected["decisions"]:
        st.subheader("Decision history")
        st.dataframe(
            pd.DataFrame([
                {
                    "From": item["previous_status"],
                    "Decision": item["new_status"],
                    "Decision maker": item["decision_by"],
                    "Rationale": item["rationale"],
                    "Date": item["decided_at"],
                }
                for item in selected["decisions"]
            ]),
            width="stretch",
            hide_index=True,
        )

    st.warning(
        "A Selected status means the factory was selected for further review only. It does not mean "
        "the supplier is qualified, approved, technically suitable, or authorized for production transfer."
    )
