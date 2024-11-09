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


# Initialize session state with default values if they are not already set
def initialize_session_state():
    # Loop through each key-value pair in the DEFAULT_VALUES dictionary
    for key, value in DEFAULT_VALUES.items():
        # Check if the key is missing from Streamlit's session state
        if key not in st.session_state:
            # If missing, set the session state key to the default value
            st.session_state[key] = value


# Function to rerun the Streamlit app, useful for refreshing the app state or UI components
# This rerun ensures compatibility with Snowflake by re-executing the app's code
def conditional_rerun():
    # Streamlit function to force a complete rerun of the app from top to bottom
    # This is often used to refresh UI elements or session state after certain events
    st.rerun()


# Function to set a reset flag in the session state, signaling that the form needs to be cleared
def clear_form():
    # Set the 'reset_flag' in Streamlit's session state to True
    # This flag can be checked elsewhere in the app to determine if the form should be cleared
    st.session_state.reset_flag = True


# Function to reset session state values to their defaults and trigger an app rerun
def reset_form():
    # Iterate over each key in the DEFAULT_VALUES dictionary
    for key in DEFAULT_VALUES.keys():
        # If the key exists in Streamlit's session state, delete it to reset its value
        if key in st.session_state:
            del st.session_state[key]

    # After resetting each value, set the 'reset_flag' in session state to False,
    # indicating that the form no longer requires clearing
    st.session_state.reset_flag = False

    # Call the conditional_rerun function to refresh the app UI and session state
    conditional_rerun()


# Function to display a dropdown (select box) for selecting a company from available options
def get_company_selection():
    # Retrieve a list of distinct company names from the data model
    companies = model.get_distinct_company_names()

    # Filter out any empty or None values from the list of company names
    filtered_companies = [company for company in companies if company]

    # Insert an empty string at the beginning of the list to provide a blank default option
    filtered_companies.insert(0, "")  # Allows users to select a blank option initially

    # Display a select box in the Streamlit UI with the list of companies
    # Label it as "Step 1 of 4: Select company" and associate it with the session state key 'selected_company'
    return st.selectbox(
        "Step 1 of 4: Select company",
        options=filtered_companies,
        key="selected_company",
    )


# Function to display a dropdown (select box) for selecting a program, only if a company is selected
def get_program_selection():
    # Check if a company has been selected in the session state
    if st.session_state.selected_company:
        # Retrieve a list of distinct program codes for the selected company
        programs = model.get_distinct_program_codes(st.session_state.selected_company)

        # Filter out any empty or None values from the list of program codes
        filtered_programs = [program for program in programs if program]

        # Insert an empty string at the beginning to provide a blank default option
        filtered_programs.insert(
            0, ""
        )  # Allows users to select a blank option initially

        # Display a select box in the Streamlit UI with the list of program codes
        # Label it as "Step 2 of 4: Select Program" and associate it with the session state key 'selected_program'
        return st.selectbox(
            "Step 2 of 4: Select Program",
            options=filtered_programs,
            key="selected_program",
        )

    # Return None if no company is selected, indicating no dropdown should be displayed
    return None


# Function to display a multiselect for selecting products, only if a program is selected
def get_product_selection():
    # Check if a program has been selected in the session state
    if st.session_state.selected_program:
        # Retrieve a list of distinct product codes for the selected program
        products = model.get_distinct_product_codes(st.session_state.selected_program)

        # Filter out any empty or None values from the list of product codes
        filtered_products = [product for product in products if product]

        # Display a multiselect box in the Streamlit UI with the list of product codes
        # Label it as "Step 3 of 4: Select Products" and associate it with the session state key 'selected_products'
        return st.multiselect(
            "Step 3 of 4: Select Products",
            options=filtered_products,
            key="selected_products",
        )

    # Return None if no program is selected, indicating no multiselect should be displayed
    return None


# Function to display a number input field for entering the commission amount, only if products are selected
def get_commission_input():
    # Check if there are any selected products in the session state
    if st.session_state.selected_products:
        # Display a number input field in the Streamlit UI using the view function
        # Label it as "Step 4 of 4: Enter COMMISSION_AMOUNT" and associate it with the session state key 'ninput_commission'
        # Set the minimum allowable value for the input to 0.0
        return view.display_number_input(
            "Step 4 of 4: Enter COMMISSION_AMOUNT",
            key="ninput_commission",
            min_value=0.0,
        )

    # Return None if no products are selected, indicating no input field should be displayed
    return None


# Function to handle form submission, including validation, duplicate checking, and saving data to the database
def handle_form_submission():
    # Check if the reset flag is set in session state; if so, reset the form to default values
    if st.session_state.get("reset_flag"):
        reset_form()

    # Display a form submit button labeled "Save Entry" and check if it's clicked
    if view.display_form_submit_button("Save Entry", form_key="ulr_form"):
        # Validate required fields: selected company, program, products, and positive commission amount
        if not (
            st.session_state.selected_company
            and st.session_state.selected_program
            and st.session_state.selected_products
            and st.session_state.ninput_commission > 0
        ):
            # Display an error message if any required field is missing or commission is not positive
            view.display_error_message(
                "Please fill all fields and provide a valid commission amount."
            )
        else:
            # Initialize timestamp for the current time to mark entry updates
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entries = []  # List to store valid new entries
            duplicate_entries = []  # List to store duplicates for feedback

            # Loop through each selected product to check for duplicates or prepare new entries
            for product in st.session_state.selected_products:
                # Check if an entry for this product already exists
                if model.check_existing_entry(
                    st.session_state.selected_company,
                    st.session_state.selected_program,
                    product,
                ):
                    duplicate_entries.append(product)  # Add product to duplicates list
                else:
                    # If not a duplicate, prepare a new entry with session state data
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

            # Display an error message if duplicates were detected
            if duplicate_entries:
                duplicate_list = ", ".join(duplicate_entries)
                view.display_error_message(
                    f"Duplicate entry detected: The product code(s) {duplicate_list} already exist \
                        for the selected company and program. Please modify your input or \
                            check existing records."
                )
                reset_form()  # Reset the form after detecting duplicates

            # Save new entries if there are any valid entries to add
            if new_entries:
                new_commision_data = pd.DataFrame(
                    new_entries
                )  # Convert entries to DataFrame format
                success, message = model.save_commission_data(
                    new_commision_data
                )  # Save to database
                if success:
                    # Display success message if save was successful
                    view.display_success_message(message)
                    reset_form()  # Reset the form after successful save
                    conditional_rerun()  # Rerun app to refresh UI
                else:
                    # Display an error message if save operation fails
                    view.display_error_message(message)


# Function to display the commission data table with filtering and editing options
def display_commission_table(max_visible_rows=25):
    # Fetch the current commission data from the Snowflake database
    commission_data = model.get_dataset("PRODUCTS.CUSTOMERS.COMMISSIONS")

    # Sidebar filters for various columns to refine data displayed in the table
    st.sidebar.header("Filter Options")
    company_filter = st.sidebar.text_input(
        "Filter by Company Name"
    )  # Text input for company name filter
    program_filter = st.sidebar.text_input(
        "Filter by Program Code"
    )  # Text input for program code filter
    product_filter = st.sidebar.text_input(
        "Filter by Product Code"
    )  # Text input for product code filter
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

    # Sidebar date range filter for filtering data by the last update date
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

    # Apply the date range filter if both start and end dates are provided
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_data = filtered_data[
            (filtered_data["UPDATED_LAST"] >= pd.to_datetime(start_date))
            & (filtered_data["UPDATED_LAST"] <= pd.to_datetime(end_date))
        ]

    # Sidebar sorting control for ordering data by key columns
    st.sidebar.header("Sorting Options")
    sort_column = st.sidebar.selectbox(
        "Sort by Column",
        options=[""] + ["COMPANY_NAME", "PROGRAM_CODE", "PRODUCT_CODE", "IS_ACTIVE"],
        index=0,  # Default to no sorting
    )

    # Apply sorting by the selected column, or default to UPDATED_LAST in descending order
    if not sort_column:
        filtered_data = filtered_data.sort_values(by="UPDATED_LAST", ascending=False)
    else:
        filtered_data = filtered_data.sort_values(by=sort_column, ascending=True)

    # Specify columns that are editable in the data editor (commission amount and active status)
    editable_columns = ["COMMISSION_AMOUNT", "IS_ACTIVE"]

    # Reset index for clean display in the data editor
    filtered_data = filtered_data.reset_index(drop=True)

    # Display the filtered data in a Streamlit data editor for interactive viewing and editing
    edited_commission_data = st.data_editor(
        filtered_data,
        use_container_width=True,
        height=600,
        num_rows="dynamic",
        disabled=filtered_data.columns.difference(editable_columns),
    )

    # Identify any rows deleted by comparing indexes before and after editing
    original_index_set = set(filtered_data.index)
    edited_index_set = set(edited_commission_data.index)
    deleted_indexes = original_index_set - edited_index_set

    # Detect any changes in editable columns or row deletions for updating or deleting entries
    if not edited_commission_data.equals(filtered_data) or deleted_indexes:
        st.write("Changes detected. Click 'Apply Changes' to save.")

        if st.button("Apply Changes"):
            try:
                # Handle deletions based on indexes of deleted rows
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

                # Handle updates for rows with modified data
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

                # Trigger a rerun to refresh the displayed data after changes are applied
                conditional_rerun()
            except Exception as e:
                st.error(f"Error applying changes: {e}")
