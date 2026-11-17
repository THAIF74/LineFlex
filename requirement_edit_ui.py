"""Streamlit editor and version-history viewer for production requirements."""

import pandas as pd
import streamlit as st

from planning import get_production_requirement, get_production_requirements
from requirement_versions import get_requirement_version_history, update_production_requirement


def _parse_csv(value):
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def render_requirement_edit_workspace():
    st.divider()
    st.subheader("Edit a Requirement & View Version History")
    records = get_production_requirements()
    if not records:
        st.info("Save a production requirement before opening the editor.")
        return

    labels = {
        item["id"]: f'{item["requirement_name"]} â€” {item["part_number"] or "No part number"} (ID {item["id"]})'
        for item in records
    }
    selected_id = st.selectbox(
        "Choose a requirement to edit",
        options=list(labels),
        format_func=lambda value: labels[value],
        key="requirement_version_editor_selection",
    )
    selected = get_production_requirement(selected_id)
    if selected is None:
        st.error("The selected requirement could not be found.")
        return

    history = get_requirement_version_history(selected_id)
    current_version = history[0]["version_number"] if history else 1
    st.caption(f"Current saved version: {current_version}. Every successful edit creates a new snapshot.")
    st.warning(
        "Editing this requirement does not automatically reopen an existing second-source "
        "qualification linked to it. Recheck prior qualification decisions before relying on them."
    )
    capabilities = selected["required_capabilities"]

    with st.form(f"edit_production_requirement_{selected_id}"):
        name = st.text_input("Requirement Name", value=selected["requirement_name"])
        part_number = st.text_input("Part Number / Reference", value=selected["part_number"])
        monthly_demand = st.number_input(
            "Required Monthly Demand", min_value=0.0,
            value=float(selected["monthly_demand"]), step=100.0,
        )
        capacity_unit = st.text_input("Demand Unit", value=selected["capacity_unit"])
        machines = st.text_input("Required Machines", value=", ".join(capabilities.get("Machine", [])))
        processes = st.text_input("Required Processes", value=", ".join(capabilities.get("Process", [])))
        materials = st.text_input("Required Materials", value=", ".join(capabilities.get("Material", [])))
        certifications = st.text_input(
            "Required Certifications", value=", ".join(capabilities.get("Certification", []))
        )
        notes = st.text_area("Notes", value=selected["notes"])
        change_note = st.text_input(
            "Reason for this change (required)",
            placeholder="Example: Updated monthly demand after planning review",
        )
        save_clicked = st.form_submit_button("Save New Version", type="primary")

    if save_clicked:
        try:
            updated = update_production_requirement(
                requirement_id=selected_id,
                requirement_name=name,
                part_number=part_number,
                monthly_demand=monthly_demand,
                capacity_unit=capacity_unit,
                notes=notes,
                required_capabilities={
                    "Machine": _parse_csv(machines),
                    "Process": _parse_csv(processes),
                    "Material": _parse_csv(materials),
                    "Certification": _parse_csv(certifications),
                },
                change_note=change_note,
            )
            if updated is None:
                st.error("The requirement no longer exists. Refresh the page and try again.")
            else:
                st.success(f"Requirement updated. Version {updated['current_version']} saved.")
                st.rerun()
        except ValueError as error:
            st.error(str(error))

    history = get_requirement_version_history(selected_id)
    st.markdown("**Saved version history**")
    if history:
        st.dataframe(
            pd.DataFrame([
                {
                    "Version": item["version_number"],
                    "Change Note": item["change_note"],
                    "Saved At": item["changed_at"],
                }
                for item in history
            ]),
            width="stretch",
            hide_index=True,
        )
        for item in history:
            with st.expander(f"Version {item['version_number']} â€” {item['change_note']}"):
                st.json(item["snapshot"])