"""Streamlit workspace for managing second-source qualification checklists."""

import pandas as pd
import streamlit as st

from database import get_factories
from planning import get_production_requirements
from qualification import (
    CHECK_STATUSES,
    DECISION_STATUSES,
    create_qualification,
    get_qualification,
    get_qualifications,
    record_qualification_decision,
    update_qualification_check,
)


def render_qualification_workspace():
    st.header("Second-Source Qualification")
    st.caption(
        "Track review tasks for an alternative factory against a production requirement. "
        "Checklist completion records human-entered progress; it does not certify a supplier."
    )

    requirements = get_production_requirements()
    factories = get_factories()

    if requirements and factories:
        requirement_labels = {
            item["id"]: f'{item["requirement_name"]} — {item["part_number"] or "No part number"} (ID {item["id"]})'
            for item in requirements
        }
        factory_labels = {
            item["id"]: f'{item["factory_name"]} — {item["city"]}, {item["state"]} (ID {item["id"]})'
            for item in factories
        }

        with st.expander("Start a qualification for an alternative factory", expanded=True):
            with st.form("create_second_source_qualification"):
                requirement_id = st.selectbox(
                    "Production requirement",
                    options=list(requirement_labels),
                    format_func=lambda value: requirement_labels[value],
                )
                factory_id = st.selectbox(
                    "Alternative factory",
                    options=list(factory_labels),
                    format_func=lambda value: factory_labels[value],
                )
                create_clicked = st.form_submit_button("Start Qualification", type="primary")

            if create_clicked:
                try:
                    qualification_id = create_qualification(requirement_id, factory_id)
                    st.success(f"Qualification started. ID: {qualification_id}")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
    else:
        st.info("Add at least one production requirement and one factory before starting a qualification.")

    records = get_qualifications()
    st.subheader("Qualification Register")
    if not records:
        st.info("No second-source qualifications have been started yet.")
        return

    st.dataframe(
        pd.DataFrame([
            {
                "ID": item["id"],
                "Requirement": item["requirement_name"],
                "Part Number": item["part_number"],
                "Alternative Factory": item["factory_name"],
                "Location": f'{item["city"]}, {item["state"]}',
                "Status": item["status"],
                "Checks Complete": f'{item["checks_passed"]}/{item["checks_total"]}',
            }
            for item in records
        ]),
        width="stretch",
        hide_index=True,
    )

    labels = {
        item["id"]: f'{item["requirement_name"]} → {item["factory_name"]} (ID {item["id"]})'
        for item in records
    }
    selected_id = st.selectbox(
        "Choose a qualification to review",
        options=list(labels),
        format_func=lambda value: labels[value],
        key="selected_qualification_id",
    )
    selected = get_qualification(selected_id)
    if selected is None:
        st.error("The selected qualification could not be found.")
        return

    st.markdown(f'### {selected["requirement_name"]} → {selected["factory_name"]}')
    st.write(f'**Part:** {selected["part_number"] or "Not specified"}')
    st.write(f'**Factory:** {selected["city"]}, {selected["state"]}')
    st.write(f'**Workflow status:** {selected["status"]}')
    st.caption("Use one form per checklist item. Dates must use YYYY-MM-DD.")

    if selected["status"] in ("Approved", "Rejected"):
        st.info("This qualification has a final decision. Its checklist is locked to preserve the decision record.")
    else:
        for check in selected["checks"]:
            with st.expander(f'{check["title"]} — {check["status"]}'):
                with st.form(f'qualification_check_{check["id"]}'):
                    status = st.selectbox(
                        "Check status",
                        options=list(CHECK_STATUSES),
                        index=CHECK_STATUSES.index(check["status"]),
                    )
                    owner = st.text_input("Owner", value=check["owner"])
                    due_date = st.text_input("Due date (YYYY-MM-DD)", value=check["due_date"])
                    evidence_reference = st.text_input(
                        "Evidence reference (file name, document ID or link)",
                        value=check["evidence_reference"],
                    )
                    notes = st.text_area("Review notes", value=check["notes"])
                    save_clicked = st.form_submit_button("Save Checklist Item")

                if save_clicked:
                    try:
                        update_qualification_check(
                            qualification_id=selected_id,
                            check_id=check["id"],
                            status=status,
                            owner=owner,
                            due_date=due_date,
                            evidence_reference=evidence_reference,
                            notes=notes,
                        )
                        st.success("Checklist item saved.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

        st.divider()
        st.subheader("Record a Human Decision")
        st.caption("Approval is blocked until every checklist item is Passed or Not applicable.")
        with st.form("qualification_decision_form"):
            decision = st.selectbox("Decision", options=list(DECISION_STATUSES))
            decision_by = st.text_input("Decision maker / team")
            decision_notes = st.text_area("Decision rationale")
            decision_clicked = st.form_submit_button("Record Decision", type="primary")

        if decision_clicked:
            try:
                record_qualification_decision(
                    qualification_id=selected_id,
                    decision=decision,
                    decision_by=decision_by,
                    decision_notes=decision_notes,
                )
                st.success(f"Decision recorded: {decision}")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

    if selected["decisions"]:
        st.subheader("Decision History")
        st.dataframe(
            pd.DataFrame([
                {
                    "From": item["previous_status"],
                    "Decision": item["new_status"],
                    "Decision By": item["decision_by"],
                    "Rationale": item["decision_notes"],
                    "Date": item["decided_at"],
                }
                for item in selected["decisions"]
            ]),
            width="stretch",
            hide_index=True,
        )

    st.warning(
        "LineFlex records qualification tasks and human decisions only. Evidence references are not "
        "independently checked. A recorded approval is not an automated certification or guarantee "
        "of engineering suitability, available capacity, supplier quality, or customer acceptance."
    )
