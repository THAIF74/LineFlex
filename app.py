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

st.set_page_config(page_title="LineFlex | Factory Registry", page_icon="🏭", layout="wide")
initialize_db()


def _parse_csv(value):
    return [part.strip() for part in value.split(",") if part.strip()]


def _join_capabilities(factory, category):
    return ", ".join(factory.get("capabilities", {}).get(category, []))


st.title("🏭 LineFlex")
st.subheader("Factory Capability Registry")
st.caption("Register and manage manufacturing capability information.")

factories = get_factories()
all_processes = {
    process
    for factory in factories
    for process in factory.get("capabilities", {}).get("Process", [])
}

metric1, metric2, metric3 = st.columns(3)
metric1.metric("Registered Factories", len(factories))
metric2.metric("Factory Locations", len({(f["city"], f["state"]) for f in factories}))
metric3.metric("Unique Processes", len(all_processes))

register_tab, directory_tab, manage_tab = st.tabs(
    ["Register Factory", "Factory Directory", "Manage Factories"]
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

                edit_machines = st.text_input(
                    "Machines", value=_join_capabilities(selected, "Machine")
                )
                edit_processes = st.text_input(
                    "Processes", value=_join_capabilities(selected, "Process")
                )
                edit_materials = st.text_input(
                    "Supported Materials", value=_join_capabilities(selected, "Material")
                )
                edit_certifications = st.text_input(
                    "Certifications", value=_join_capabilities(selected, "Certification")
                )
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

st.divider()
st.caption(
    "LineFlex is an early prototype. Capacity and capability details are user-entered "
    "and are not independently verified. Similar equipment or stated capacity does not "
    "prove technical compatibility or supplier approval."
)
