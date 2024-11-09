import os
import time
import streamlit as st  # Required for session state and form controls
import pandas as pd
from datetime import datetime
import views.app_view as view
import models.data_model as model

# Default values for session state, including company, program, product selections,
# commission input, and reset flag for clearing form data.
DEFAULT_VALUES = {
    "selected_company": "",
    "selected_program": "",
    "selected_products": [],  # Initialize selected_products as an empty list
    "ninput_commission": 0.0,
    "is_active": True,
    "reset_flag": False,
}


# Initialize session state with default values if not already set
def initialize_session_state():
    for key, value in DEFAULT_VALUES.items():
        if key not in st.session_state:
            st.session_state[key] = value


# Rerun the app if needed, ensuring compatibility with Snowflake
def conditional_rerun():
    st.rerun()


# Initialize the page layout and title
def initialize_page():
    view.set_page_config()
    view.display_title("Ultimate Loss Ratio Form Entry")


# Set reset flag in session state to indicate form clearing
def clear_form():
    st.session_state.reset_flag = True


# Reset session state to default values and trigger rerun to refresh UI
def reset_form():
    for key in DEFAULT_VALUES.keys():
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.reset_flag = False
    conditional_rerun()


# Display a select box for each step in the process, customizing label and options
def get_selection_step(step_label, options, session_key):
    options = (
        [""] + options
        if options
        else [f"No {step_label.split()[3].lower()}s available"]
    )
    selected = view.display_selectbox(
        f"Step {step_label}",
        options=options,
        key=session_key,
    )
    return selected


# Display the dropdown for selecting a company from available options
def get_company_selection():
    companies = model.get_distinct_company_names()
    filtered_companies = [company for company in companies if company]
    filtered_companies.insert(0, "")  # Add a blank option at the beginning
    return st.selectbox(
        "Step 1 of 4: Select company",
        options=filtered_companies,
        key="selected_company",
    )


# Display the dropdown for selecting a program, only if a company is selected
def get_program_selection():
    if st.session_state.selected_company:
        programs = model.get_distinct_program_codes(st.session_state.selected_company)
        filtered_programs = [program for program in programs if program]
        filtered_programs.insert(0, "")  # Add a blank option at the beginning
        return st.selectbox(
            "Step 2 of 4: Select Program",
            options=filtered_programs,
            key="selected_program",
        )
    return None


# Display a multiselect for selecting products if a program is selected
def get_product_selection():
    if st.session_state.selected_program:
        products = model.get_distinct_product_codes(st.session_state.selected_program)
        filtered_products = [product for product in products if product]
        return st.multiselect(
            "Step 3 of 4: Select Products",
            options=filtered_products,
            key="selected_products",
        )
    return None


# Display number input for commission amount, only if multiple products are selected
def get_commission_input():
    if st.session_state.selected_products:
        return view.display_number_input(
            "Step 4 of 4: Enter COMMISSION_AMOUNT",
            key="ninput_commission",
            min_value=0.0,
        )
    return None


# Handle the form submission logic, including validation, duplicate check, and data save
def handle_form_submission():
    if st.session_state.get("reset_flag"):
        reset_form()

    if view.display_form_submit_button("Save Entry", form_key="ulr_form"):
        # Validate all required fields and commission amount
        if not (
            st.session_state.selected_company
            and st.session_state.selected_program
            and st.session_state.selected_products
            and st.session_state.ninput_commission > 0
        ):
            view.display_error_message(
                "Please fill all fields and provide a valid commission amount."
            )
        else:
            # Prepare to save entries, checking for duplicates and gathering valid entries
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entries = []
            duplicate_entries = []

            # Loop through each product to detect duplicates or prepare new entries
            for product in st.session_state.selected_products:
                if model.check_existing_entry(
                    st.session_state.selected_company,
                    st.session_state.selected_program,
                    product,
                ):
                    duplicate_entries.append(product)  # Collect duplicates
                else:
                    new_entries.append(
                        {
                            "COMPANY_NAME": st.session_state.selected_company,
                            "PROGRAM_CODE": st.session_state.selected_program,
                            "PRODUCT_CODE": product,
                            "COMMISSION_AMOUNT": st.session_state.ninput_commission,
                            "IS_ACTIVE": st.session_state.is_active,
                            "UPDATED_LAST": current_time,
                            "USERNAME": st.experimental_user.get(
                                "user_name", "TEST_USER"
                            ),
                        }
                    )

            # Display error message if duplicates are found
            if duplicate_entries:
                duplicate_list = ", ".join(duplicate_entries)
                view.display_error_message(
                    f"Duplicate entry detected: The product code(s) {duplicate_list} already exist \
                        for the selected company and program. Please modify your input or \
                            check existing records."
                )
                reset_form()  # Reset after detecting only duplicates

            # Save new entries if there are any
            if new_entries:
                new_commision_data = pd.DataFrame(new_entries)
                success, message = model.save_commission_data(new_commision_data)
                if success:
                    view.display_success_message(message)
                    reset_form()  # Reset after successful save
                    conditional_rerun()
                else:
                    view.display_error_message(message)


# Display the commission data table with options for filtering and editing
def display_commission_table(max_visible_rows=25):
    # Fetch the current ULR data from Snowflake
    commission_data = model.get_dataset("PRODUCTS.CUSTOMERS.COMMISSIONS")

    # Sidebar filtering controls for various columns
    st.sidebar.header("Filter Options")
    company_filter = st.sidebar.text_input("Filter by Company Name")
    program_filter = st.sidebar.text_input("Filter by Program Code")
    product_filter = st.sidebar.text_input("Filter by Product Code")
    company_min_filter = st.sidebar.number_input(
        "Min Commission",
        value=commission_data["COMMISSION_AMOUNT"].min(),
        step=0.01,
    )
    commission_max_filter = st.sidebar.number_input(
        "Max Commission",
        value=commission_data["COMMISSION_AMOUNT"].max(),
        step=0.01,
    )
    username_filter = st.sidebar.selectbox(
        "Filter by Username", options=[""] + list(commission_data["USERNAME"].unique())
    )

    # Date range slider for filtering by update date
    st.sidebar.header("Date Filter")
    date_range = st.sidebar.date_input("Filter by Updated Date", [])

    # Apply filters to the data based on user input
    filtered_data = commission_data
    if company_filter:
        filtered_data = filtered_data[
            filtered_data["COMPANY_NAME"].str.contains(
                company_filter, case=False, na=False
            )
        ]
    if program_filter:
        filtered_data = filtered_data[
            filtered_data["PROGRAM_CODE"].str.contains(
                program_filter, case=False, na=False
            )
        ]
    if product_filter:
        filtered_data = filtered_data[
            filtered_data["PRODUCT_CODE"].str.contains(
                product_filter, case=False, na=False
            )
        ]
    if company_min_filter is not None:
        filtered_data = filtered_data[
            filtered_data["COMMISSION_AMOUNT"] >= company_min_filter
        ]
    if commission_max_filter is not None:
        filtered_data = filtered_data[
            filtered_data["COMMISSION_AMOUNT"] <= commission_max_filter
        ]
    if username_filter:
        filtered_data = filtered_data[filtered_data["USERNAME"] == username_filter]

    # Date range filter application
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_data = filtered_data[
            (filtered_data["UPDATED_LAST"] >= pd.to_datetime(start_date))
            & (filtered_data["UPDATED_LAST"] <= pd.to_datetime(end_date))
        ]

    # Sorting controls for key columns
    st.sidebar.header("Sorting Options")
    sort_column = st.sidebar.selectbox(
        "Sort by Column",
        options=[""] + ["COMPANY_NAME", "PROGRAM_CODE", "PRODUCT_CODE", "IS_ACTIVE"],
        index=0,
    )

    # Default sorting by UPDATED_LAST in descending order if no column is selected
    if not sort_column:
        filtered_data = filtered_data.sort_values(by="UPDATED_LAST", ascending=False)
    else:
        filtered_data = filtered_data.sort_values(by=sort_column, ascending=True)

    # Define editable columns for the data editor
    editable_columns = ["COMMISSION_AMOUNT", "IS_ACTIVE"]

    # Reset index before displaying data in editor
    filtered_data = filtered_data.reset_index(drop=True)

    edited_commission_data = st.data_editor(
        filtered_data,
        use_container_width=True,
        height=600,
        num_rows="dynamic",
        disabled=filtered_data.columns.difference(editable_columns),
    )

    # Check for deleted rows based on index changes
    original_index_set = set(filtered_data.index)
    edited_index_set = set(edited_commission_data.index)
    deleted_indexes = original_index_set - edited_index_set

    # Detect and handle any changes in editable columns or row deletions
    if not edited_commission_data.equals(filtered_data) or deleted_indexes:
        st.write("Changes detected. Click 'Apply Changes' to save.")

        if st.button("Apply Changes"):
            try:
                # Handle deletions based on deleted row indexes
                for delete_index in deleted_indexes:
                    row_to_delete = filtered_data.loc[delete_index]
                    success, message = model.delete_commission_data(
                        company_name=row_to_delete["COMPANY_NAME"],
                        program_code=row_to_delete["PROGRAM_CODE"],
                        product_code=row_to_delete["PRODUCT_CODE"],
                    )
                    if success:
                        st.success(
                            f"Row for company '{row_to_delete['COMPANY_NAME']}' \
                                deleted successfully."
                        )
                    else:
                        st.error(f"Failed to delete row: {message}")

                # Handle updates based on changes in editable columns
                changed_rows = edited_commission_data[
                    edited_commission_data.ne(filtered_data).any(axis=1)
                ]
                for index, row in changed_rows.iterrows():
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    success, message = model.update_ulr_data(
                        company_name=row["COMPANY_NAME"],
                        program_code=row["PROGRAM_CODE"],
                        product_code=row["PRODUCT_CODE"],
                        commission_amount=row["COMMISSION_AMOUNT"],
                        is_active=row["IS_ACTIVE"],
                        updated_last=current_time,
                        username=st.experimental_user.get("user_name", "Unknown"),
                    )
                    if success:
                        st.success(
                            f"Row for company '{row['COMPANY_NAME']}' updated successfully."
                        )
                    else:
                        st.error(f"Failed to update row: {message}")

                # Trigger rerun to refresh the displayed data
                conditional_rerun()
            except Exception as e:
                st.error(f"Error applying changes: {e}")
