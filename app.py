import pandas as pd
import streamlit as st

from database import (
    add_factory,
    delete_factory,
    get_factories,
    get_factory_by_id,
    initialize_db,
    update_factory,
)
from planning import (
    add_production_requirement,
    compare_requirement_to_factories,
    get_production_requirements,
    initialize_planning_tables,
)
from qualification import initialize_qualification_tables
from qualification_ui import render_qualification_workspace
from requirement_edit_ui import render_requirement_edit_workspace

st.set_page_config(page_title="LineFlex | Factory Registry", page_icon="🏭", layout="wide")
initialize_db()
initialize_planning_tables()
initialize_qualification_tables()


def _parse_csv(value):
    return [part.strip() for part in value.split(",") if part.strip()]


def _join_capabilities(factory, category):
    return ", ".join(factory.get("capabilities", {}).get(category, []))


st.title("🏭 LineFlex")
st.subheader("Factory Capability Registry & Production Readiness")
st.caption("Record factory capabilities, define production requirements and compare recorded information.")

factories = get_factories()
all_processes = {
    process
    for factory in factories
    for process in factory.get("capabilities", {}).get("Process", [])
}

metric1, metric2, metric3, metric4 = st.columns(4)
metric1.metric("Registered Factories", len(factories))
metric2.metric("Factory Locations", len({(f["city"], f["state"]) for f in factories}))
metric3.metric("Unique Processes", len(all_processes))
metric4.metric("Production Requirements", len(get_production_requirements()))

register_tab, directory_tab, manage_tab, requirement_tab, matching_tab, qualification_tab = st.tabs(
    ["Register Factory", "Factory Directory", "Manage Factories", "Production Requirements", "Capability Matching", "Second-Source Qualification"]
)

with register_tab:
    st.header("Register a Factory")
    with st.form("factory_registration", clear_on_submit=True):
        factory_name = st.text_input("Factory Name")
        col1, col2 = st.columns(2)
        with col1:
            city = st.text_input("City")
        with col2:
            state = st.text_input("State")

        col1, col2 = st.columns(2)
        with col1:
            monthly_capacity = st.number_input(
                "Monthly Capacity", min_value=0.0, value=1000.0, step=100.0
            )
        with col2:
            capacity_unit = st.selectbox(
                "Capacity Unit", ["Units", "Pieces", "Tons", "Components"]
            )

        st.subheader("Manufacturing Capabilities")
        machines = st.text_input("Machines", placeholder="CNC Lathe, VMC")
        processes = st.text_input("Processes", placeholder="Turning, Milling")
        materials = st.text_input("Supported Materials", placeholder="Aluminium, Steel")
        certifications = st.text_input(
            "Certifications", placeholder="ISO 9001, IATF 16949"
        )
        submitted = st.form_submit_button("Register Factory", type="primary")

    if submitted:
        try:
            factory_id = add_factory(
                factory_name=factory_name,
                city=city,
                state=state,
                monthly_capacity=monthly_capacity,
                capacity_unit=capacity_unit,
                machines=_parse_csv(machines),
                processes=_parse_csv(processes),
                materials=_parse_csv(materials),
                certifications=_parse_csv(certifications),
            )
            st.success(f"Factory registered successfully. ID: {factory_id}")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

with directory_tab:
    st.header("Factory Directory")
    search = st.text_input(
        "Search by factory name, city or state", placeholder="Enter search term..."
    )
    filtered = get_factories(search)

    if not filtered:
        st.info("No factories found. Register a factory to get started.")
    else:
        table_data = [
            {
                "ID": f["id"],
                "Factory": f["factory_name"],
                "City": f["city"],
                "State": f["state"],
                "Monthly Capacity": f'{f["monthly_capacity"]:,.2f} {f["capacity_unit"]}',
                "Processes": _join_capabilities(f, "Process"),
            }
            for f in filtered
        ]
        st.dataframe(pd.DataFrame(table_data), width="stretch", hide_index=True)

        for factory in filtered:
            with st.expander(f'{factory["factory_name"]} — {factory["city"]} (ID {factory["id"]})'):
                st.write(f'**Location:** {factory["city"]}, {factory["state"]}')
                st.write(
                    f'**Monthly stated capacity:** {factory["monthly_capacity"]:,.2f} '
                    f'{factory["capacity_unit"]}'
                )
                for category, values in factory["capabilities"].items():
                    st.write(f"**{category}:** {', '.join(values) or 'Not provided'}")

with manage_tab:
    st.header("Edit or Delete a Factory")
    if not factories:
        st.info("There are no factory records to manage yet.")
    else:
        labels = {
            f'{factory["factory_name"]} — {factory["city"]} (ID {factory["id"]})': factory["id"]
            for factory in factories
        }
        selected_label = st.selectbox("Choose a factory", list(labels.keys()))
        selected_id = labels[selected_label]
        selected = get_factory_by_id(selected_id)

        if selected:
            st.subheader("Update Factory Details")
            with st.form("edit_factory"):
                edit_name = st.text_input("Factory Name", value=selected["factory_name"])
                col1, col2 = st.columns(2)
                with col1:
                    edit_city = st.text_input("City", value=selected["city"])
                with col2:
                    edit_state = st.text_input("State", value=selected["state"])

                col1, col2 = st.columns(2)
                with col1:
                    edit_capacity = st.number_input(
                        "Monthly Capacity",
                        min_value=0.0,
                        value=float(selected["monthly_capacity"]),
                        step=100.0,
                    )
                with col2:
                    units = ["Units", "Pieces", "Tons", "Components"]
                    current_unit = selected["capacity_unit"]
                    unit_options = units if current_unit in units else [current_unit] + units
                    edit_unit = st.selectbox(
                        "Capacity Unit", unit_options, index=unit_options.index(current_unit)
                    )

                edit_machines = st.text_input("Machines", value=_join_capabilities(selected, "Machine"))
                edit_processes = st.text_input("Processes", value=_join_capabilities(selected, "Process"))
                edit_materials = st.text_input("Supported Materials", value=_join_capabilities(selected, "Material"))
                edit_certifications = st.text_input("Certifications", value=_join_capabilities(selected, "Certification"))
                update_clicked = st.form_submit_button("Save Changes", type="primary")

            if update_clicked:
                try:
                    updated = update_factory(
                        factory_id=selected_id,
                        factory_name=edit_name,
                        city=edit_city,
                        state=edit_state,
                        monthly_capacity=edit_capacity,
                        capacity_unit=edit_unit,
                        machines=_parse_csv(edit_machines),
                        processes=_parse_csv(edit_processes),
                        materials=_parse_csv(edit_materials),
                        certifications=_parse_csv(edit_certifications),
                    )
                    if updated:
                        st.success("Factory details updated.")
                        st.rerun()
                    else:
                        st.error("Factory record was not found.")
                except ValueError as error:
                    st.error(str(error))

            st.divider()
            st.subheader("Delete Factory")
            with st.form("delete_factory"):
                confirm_delete = st.checkbox(
                    f'I understand that factory "{selected["factory_name"]}" and its capability entries will be deleted.'
                )
                delete_clicked = st.form_submit_button("Delete Factory")

            if delete_clicked:
                if not confirm_delete:
                    st.error("Please confirm deletion before continuing.")
                elif delete_factory(selected_id):
                    st.success("Factory and its capability entries deleted.")
                    st.rerun()
                else:
                    st.error("Factory record was not found.")

with requirement_tab:
    st.header("Define a Production Requirement")
    st.write("Describe what a part or production job requires. Use comma-separated capability labels.")
    with st.form("production_requirement_form", clear_on_submit=True):
        requirement_name = st.text_input("Requirement Name", placeholder="Aluminium Housing — CNC turning")
        part_number = st.text_input("Part Number / Reference", placeholder="PART-001")
        col1, col2 = st.columns(2)
        with col1:
            monthly_demand = st.number_input("Required Monthly Demand", min_value=0.0, value=1000.0, step=100.0)
        with col2:
            requirement_unit = st.selectbox("Demand Unit", ["Units", "Pieces", "Tons", "Components"], key="req_unit")
        st.subheader("Required Capabilities")
        required_machines = st.text_input("Required Machines", placeholder="CNC Lathe")
        required_processes = st.text_input("Required Processes", placeholder="Turning")
        required_materials = st.text_input("Required Materials", placeholder="Aluminium")
        required_certifications = st.text_input("Required Certifications", placeholder="ISO 9001")
        requirement_notes = st.text_area("Notes", placeholder="Optional part, tolerance or sourcing context")
        requirement_submitted = st.form_submit_button("Save Production Requirement", type="primary")

    if requirement_submitted:
        try:
            new_id = add_production_requirement(
                requirement_name=requirement_name,
                part_number=part_number,
                monthly_demand=monthly_demand,
                capacity_unit=requirement_unit,
                notes=requirement_notes,
                required_capabilities={
                    "Machine": _parse_csv(required_machines),
                    "Process": _parse_csv(required_processes),
                    "Material": _parse_csv(required_materials),
                    "Certification": _parse_csv(required_certifications),
                },
            )
            st.success(f"Requirement saved. ID: {new_id}")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

    saved_requirements = get_production_requirements()
    st.subheader("Saved Requirements")
    if saved_requirements:
        st.dataframe(
            pd.DataFrame([
                {"ID": item["id"], "Requirement": item["requirement_name"],
                 "Part Number": item["part_number"], "Monthly Demand": item["monthly_demand"],
                 "Unit": item["capacity_unit"]}
                for item in saved_requirements
            ]), width="stretch", hide_index=True
        )
    else:
        st.info("No production requirements have been saved yet.")

    render_requirement_edit_workspace()

with matching_tab:
    st.header("Compare Requirements with Factory Capabilities")
    saved_requirements = get_production_requirements()
    if not saved_requirements:
        st.info("Create a production requirement first.")
    elif not factories:
        st.info("Register at least one factory before running a comparison.")
    else:
        requirement_labels = {
            f'{item["requirement_name"]} — {item["part_number"] or "No part number"} (ID {item["id"]})': item["id"]
            for item in saved_requirements
        }
        chosen_label = st.selectbox("Choose a production requirement", list(requirement_labels.keys()))
        chosen_id = requirement_labels[chosen_label]
        comparison = compare_requirement_to_factories(chosen_id)
        req = comparison["requirement"]
        st.write(f'**Monthly demand:** {req["monthly_demand"]:,.2f} {req["capacity_unit"]}')
        st.write("**Required capabilities:**")
        for category, values in req["required_capabilities"].items():
            if values:
                st.write(f"- **{category}:** {', '.join(values)}")

        summary_rows = [
            {"Factory": result["factory_name"], "Location": f'{result["city"]}, {result["state"]}',
             "Overall Result": result["overall_status"], "Stated Capacity": f'{result["stated_monthly_capacity"]:,.2f} {result["factory_capacity_unit"]}',
             "Capacity Check": result["capacity_status"]}
            for result in comparison["results"]
        ]
        st.dataframe(pd.DataFrame(summary_rows), width="stretch", hide_index=True)

        for result in comparison["results"]:
            with st.expander(f'{result["factory_name"]} — {result["overall_status"]}'):
                st.write(f'**Location:** {result["city"]}, {result["state"]}')
                st.write(f'**Capacity check:** {result["capacity_status"]}')
                for category, detail in result["capability_results"].items():
                    if detail["status"] != "not_required":
                        st.write(f'**{category}: {detail["status"]}**')
                        st.write(f'  Required: {", ".join(detail["required"])}')
                        st.write(f'  Matched: {", ".join(detail["matched"]) or "None"}')
                        st.write(f'  Missing / not recorded: {", ".join(detail["missing"]) or "None"}')
        st.warning(comparison["limitation"])

with qualification_tab:
    render_qualification_workspace()

st.divider()
st.caption(
    "LineFlex is an early prototype. Capacity and capability details are user-entered "
    "and are not independently verified. A potential match is only a preliminary screen, "
    "not proof of actual availability, technical compatibility or supplier approval."
)
