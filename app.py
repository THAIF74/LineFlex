import streamlit as st
import pandas as pd

from database import initialize_db, add_factory, get_factories

st.set_page_config(
    page_title="LineFlex | Factory Registry",
    page_icon="🏭",
    layout="wide",
)

initialize_db()

st.title("🏭 LineFlex")
st.subheader("Factory Capability Registry")
st.caption("Register and manage manufacturing capability information.")

st.divider()

# Dashboard metrics
factories = get_factories()

col1, col2, col3 = st.columns(3)

col1.metric("Registered Factories", len(factories))

total_capacity = sum(
    factory["monthly_capacity"] for factory in factories
)
col2.metric("Combined Monthly Capacity", f"{total_capacity:,.0f}")

all_processes = {
    process
    for factory in factories
    for process in factory["capabilities"].get("Process", [])
}
col3.metric("Unique Processes", len(all_processes))

st.divider()

# Factory registration
st.header("Register a Factory")

with st.form("factory_registration", clear_on_submit=True):

    factory_name = st.text_input("Factory Name")

    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("City")
    with col2:
        state = st.text_input("State")

    st.subheader("Production Capacity")

    col1, col2 = st.columns(2)
    with col1:
        monthly_capacity = st.number_input(
            "Monthly Capacity",
            min_value=0.0,
            value=1000.0,
            step=100.0,
        )
    with col2:
        capacity_unit = st.selectbox(
            "Capacity Unit",
            ["Units", "Pieces", "Tons", "Components"],
        )

    st.subheader("Manufacturing Capabilities")

    machines = st.text_input(
        "Machines",
        placeholder="CNC Lathe, Milling Machine, VMC",
    )

    processes = st.text_input(
        "Processes",
        placeholder="CNC Machining, Turning, Milling",
    )

    materials = st.text_input(
        "Supported Materials",
        placeholder="Aluminium, Stainless Steel, Brass",
    )

    certifications = st.text_input(
        "Certifications",
        placeholder="ISO 9001, IATF 16949",
    )

    submitted = st.form_submit_button(
        "Register Factory",
        type="primary",
    )

    if submitted:
        try:
            if not all([
                factory_name.strip(),
                city.strip(),
                state.strip(),
            ]):
                raise ValueError(
                    "Please enter factory name, city and state."
                )

            if monthly_capacity <= 0:
                raise ValueError(
                    "Monthly capacity must be greater than zero."
                )

            factory_id = add_factory(
                factory_name=factory_name,
                city=city,
                state=state,
                monthly_capacity=monthly_capacity,
                capacity_unit=capacity_unit,
                machines=machines.split(","),
                processes=processes.split(","),
                materials=materials.split(","),
                certifications=certifications.split(","),
            )

            st.success(
                f"Factory registered successfully! ID: {factory_id}"
            )
            st.rerun()

        except ValueError as error:
            st.error(str(error))


st.divider()

# Factory directory
st.header("Factory Directory")

search = st.text_input(
    "Search by factory name, city or state",
    placeholder="Enter search term...",
)

filtered_factories = get_factories(search)

if not filtered_factories:
    st.info("No factories found. Register your first factory above.")

else:
    table_data = []

    for factory in filtered_factories:
        table_data.append({
            "Factory": factory["factory_name"],
            "City": factory["city"],
            "State": factory["state"],
            "Monthly Capacity": (
                f'{factory["monthly_capacity"]:,.0f} '
                f'{factory["capacity_unit"]}'
            ),
            "Processes": ", ".join(
                factory["capabilities"].get("Process", [])
            ),
        })

    st.dataframe(
        pd.DataFrame(table_data),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Factory Details")

    for factory in filtered_factories:
        with st.expander(
            f'{factory["factory_name"]} — {factory["city"]}'
        ):
            st.write(
                f'**Location:** {factory["city"]}, {factory["state"]}'
            )
            st.write(
                f'**Monthly Capacity:** '
                f'{factory["monthly_capacity"]:,.0f} '
                f'{factory["capacity_unit"]}'
            )

            for category, values in factory["capabilities"].items():
                st.write(f"**{category}:** {', '.join(values)}")
