import os
import time
import streamlit as st  # Required for session state and form controls
import pandas as pd
from datetime import datetime
import views.app_view as view
import models.data_model as model

DEFAULT_VALUES = {
    "selected_producer": "",
    "selected_program": "",
    "selected_products": [],  # Initialize selected_products as an empty list
    "ninput_ulr": 0.0,
    "is_active": True,
    "reset_flag": False,
}


def initialize_session_state():
    for key, value in DEFAULT_VALUES.items():
        if key not in st.session_state:
            st.session_state[key] = value


def conditional_rerun():
    # Use experimental_rerun only, ensuring compatibility with Snowflake
    st.rerun()


def initialize_page():
    view.set_page_config()
    view.display_title("Ultimate Loss Ratio Form Entry")


def clear_form():
    st.session_state.reset_flag = True


def reset_form():
    for key in DEFAULT_VALUES.keys():
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.reset_flag = False
    conditional_rerun()


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


def get_producer_selection():
    producers = model.get_distinct_producer_names()
    filtered_producers = [producer for producer in producers if producer]
    # Add a blank option at the beginning
    filtered_producers.insert(0, "")
    return st.selectbox(
        "Step 1 of 4: Select Producer",
        options=filtered_producers,
        key="selected_producer",
    )


def get_program_selection():
    if st.session_state.selected_producer:
        programs = model.get_distinct_program_codes(st.session_state.selected_producer)
        filtered_programs = [program for program in programs if program]
        # Add a blank option at the beginning
        filtered_programs.insert(0, "")
        return st.selectbox(
            "Step 2 of 4: Select Program",
            options=filtered_programs,
            key="selected_program",
        )
    return None


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


def get_ulr_input():
    # Ensure we only proceed if multiple products are selected
    if st.session_state.selected_products:
        return view.display_number_input(
            "Step 4 of 4: Enter ULTIMATE_LOSS_RATIO", key="ninput_ulr", min_value=0.0
        )
    return None


def handle_form_submission():
    if st.session_state.get("reset_flag"):
        reset_form()

    if view.display_form_submit_button("Save Entry", form_key="ulr_form"):
        if not (
            st.session_state.selected_producer
            and st.session_state.selected_program
            and st.session_state.selected_products
            and st.session_state.ninput_ulr > 0
        ):
            view.display_error_message(
                "Please fill all fields and provide a valid ULR value."
            )
        else:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entries = []
            duplicate_entries = []

            # Loop through each product and check for duplicates
            for product in st.session_state.selected_products:
                if model.check_existing_entry(
                    st.session_state.selected_producer,
                    st.session_state.selected_program,
                    product,
                ):
                    duplicate_entries.append(product)  # Collect duplicates for feedback
                else:
                    new_entries.append(
                        {
                            "PRODUCER_NAME": st.session_state.selected_producer,
                            "PROGRAM_CODE": st.session_state.selected_program,
                            "PRODUCT_CODE": product,
                            "ULTIMATE_LOSS_RATIO": st.session_state.ninput_ulr,
                            "IS_ACTIVE": st.session_state.is_active,
                            "UPDATED_LAST": current_time,
                            "USERNAME": st.experimental_user.get(
                                "user_name", "TEST_USER"
                            ),
                        }
                    )

            # Display an error message if duplicates are found
            if duplicate_entries:
                duplicate_list = ", ".join(duplicate_entries)
                view.display_error_message(
                    f"Duplicate entry detected: The product code(s) {duplicate_list} already exist \
                        for the selected producer and program. Please modify your input or \
                            check existing records."
                )
                reset_form()  # Reset after detecting only duplicates

            # Convert to DataFrame and save if there are new entries
            if new_entries:
                new_ulr_data = pd.DataFrame(new_entries)
                success, message = model.save_ulr_data(new_ulr_data)
                if success:
                    view.display_success_message(message)
                    reset_form()  # Reset after successful save
                    conditional_rerun()
                else:
                    view.display_error_message(message)


# def handle_form_submission():
#     if st.session_state.get("reset_flag"):
#         reset_form()

#     if view.display_form_submit_button("Save Entry", form_key="ulr_form"):
#         if not (
#             st.session_state.selected_producer
#             and st.session_state.selected_program
#             and st.session_state.selected_products
#             and st.session_state.ninput_ulr > 0
#         ):
#             view.display_error_message(
#                 "Please fill all fields and provide a valid ULR value."
#             )
#         else:
#             current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             new_entries = []

#             # Loop through each product and check for duplicates
#             for product in st.session_state.selected_products:
#                 if not model.check_existing_entry(
#                     st.session_state.selected_producer,
#                     st.session_state.selected_program,
#                     product,
#                 ):
#                     new_entries.append(
#                         {
#                             "PRODUCER_NAME": st.session_state.selected_producer,
#                             "PROGRAM_CODE": st.session_state.selected_program,
#                             "PRODUCT_CODE": product,
#                             "ULTIMATE_LOSS_RATIO": st.session_state.ninput_ulr,
#                             "IS_ACTIVE": st.session_state.is_active,
#                             "UPDATED_LAST": current_time,
#                             "USERNAME": st.experimental_user.get(
#                                 "user_name", "TEST_USER"
#                             ),
#                         }
#                     )

#             # Convert to DataFrame and save if there are new entries
#             if new_entries:
#                 new_ulr_data = pd.DataFrame(new_entries)
#                 success, message = model.save_ulr_data(new_ulr_data)
#                 if success:
#                     view.display_success_message(message)
#                     reset_form()  # Reset after successful save
#                     conditional_rerun()
#                 else:
#                     view.display_error_message(message)
#             else:
#                 view.display_error_message("Duplicate detected, record already exists.")
#                 reset_form()  # Reset after detecting only duplicates


def display_ulr_table(max_visible_rows=25):
    # Fetch the current ULR data from Snowflake
    ulr_data = model.get_dataset("DE_STREAMLIT_DEV.FINANCE.ULTIMATE_LOSS_RATIO")

    # Sidebar Filtering Controls
    st.sidebar.header("Filter Options")
    producer_filter = st.sidebar.text_input("Filter by Producer Name")
    program_filter = st.sidebar.text_input("Filter by Program Code")
    product_filter = st.sidebar.text_input("Filter by Product Code")
    ulr_min_filter = st.sidebar.number_input(
        "Min Ultimate Loss Ratio",
        value=ulr_data["ULTIMATE_LOSS_RATIO"].min(),
        step=0.01,
    )
    ulr_max_filter = st.sidebar.number_input(
        "Max Ultimate Loss Ratio",
        value=ulr_data["ULTIMATE_LOSS_RATIO"].max(),
        step=0.01,
    )
    username_filter = st.sidebar.selectbox(
        "Filter by Username", options=[""] + list(ulr_data["USERNAME"].unique())
    )

    # Date Range Slider for UPDATED_LAST column with no default value
    st.sidebar.header("Date Filter")
    date_range = st.sidebar.date_input("Filter by Updated Date", [])

    # Apply filters to the data
    filtered_data = ulr_data
    if producer_filter:
        filtered_data = filtered_data[
            filtered_data["PRODUCER_NAME"].str.contains(
                producer_filter, case=False, na=False
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
    if ulr_min_filter is not None:
        filtered_data = filtered_data[
            filtered_data["ULTIMATE_LOSS_RATIO"] >= ulr_min_filter
        ]
    if ulr_max_filter is not None:
        filtered_data = filtered_data[
            filtered_data["ULTIMATE_LOSS_RATIO"] <= ulr_max_filter
        ]
    if username_filter:
        filtered_data = filtered_data[filtered_data["USERNAME"] == username_filter]
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_data = filtered_data[
            (filtered_data["UPDATED_LAST"] >= pd.to_datetime(start_date))
            & (filtered_data["UPDATED_LAST"] <= pd.to_datetime(end_date))
        ]

    # Sorting Controls for Producer Name, Program Code, Product Code
    st.sidebar.header("Sorting Options")
    sort_column = st.sidebar.selectbox(
        "Sort by Column",
        options=[""] + ["PRODUCER_NAME", "PROGRAM_CODE", "PRODUCT_CODE", "IS_ACTIVE"],
        index=0,  # Default to an empty option, meaning no sorting applied initially
    )

    # Apply default sorting by UPDATED_LAST in descending order if no column is selected
    if not sort_column:
        filtered_data = filtered_data.sort_values(by="UPDATED_LAST", ascending=False)
    else:
        # Apply Sorting in Ascending Order if a Column is Selected
        filtered_data = filtered_data.sort_values(by=sort_column, ascending=True)

    # # Display the full filtered data without pagination
    editable_columns = ["ULTIMATE_LOSS_RATIO", "IS_ACTIVE"]

    # Before displaying in data_editor
    filtered_data = filtered_data.reset_index(drop=True)

    # Set the height based on the max_visible_rows
    # row_height = 35  # Average row height in pixels
    # editor_height = min(len(filtered_data), max_visible_rows) * row_height

    edited_ulr_data = st.data_editor(
        filtered_data,
        use_container_width=True,
        height=600,
        num_rows="dynamic",
        disabled=filtered_data.columns.difference(editable_columns),
    )

    # Check if rows were deleted by comparing the indexes
    original_index_set = set(filtered_data.index)
    edited_index_set = set(edited_ulr_data.index)
    deleted_indexes = original_index_set - edited_index_set

    # Check if there are any changes to the editable columns or rows have been deleted
    if not edited_ulr_data.equals(filtered_data) or deleted_indexes:
        st.write("Changes detected. Click 'Apply Changes' to save.")

        if st.button("Apply Changes"):
            try:
                # Handle Deletions
                for delete_index in deleted_indexes:
                    row_to_delete = filtered_data.loc[delete_index]
                    # Use the primary keys (PRODUCER_NAME, PROGRAM_CODE, PRODUCT_CODE)
                    # to identify the record to delete
                    success, message = model.delete_ulr_data(
                        producer_name=row_to_delete["PRODUCER_NAME"],
                        program_code=row_to_delete["PROGRAM_CODE"],
                        product_code=row_to_delete["PRODUCT_CODE"],
                    )
                    if success:
                        st.success(
                            f"Row for producer '{row_to_delete['PRODUCER_NAME']}' \
                                deleted successfully."
                        )
                    else:
                        st.error(f"Failed to delete row: {message}")

                # Handle Updates
                changed_rows = edited_ulr_data[
                    edited_ulr_data.ne(filtered_data).any(axis=1)
                ]
                for index, row in changed_rows.iterrows():
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # Use the primary keys (PRODUCER_NAME, PROGRAM_CODE, PRODUCT_CODE)
                    # to identify the record to update
                    success, message = model.update_ulr_data(
                        producer_name=row["PRODUCER_NAME"],
                        program_code=row["PROGRAM_CODE"],
                        product_code=row["PRODUCT_CODE"],
                        ultimate_loss_ratio=row["ULTIMATE_LOSS_RATIO"],
                        is_active=row["IS_ACTIVE"],
                        updated_last=current_time,
                        username=st.experimental_user.get("user_name", "Unknown"),
                    )
                    if success:
                        st.success(
                            f"Row for producer '{row['PRODUCER_NAME']}' updated successfully."
                        )
                    else:
                        st.error(f"Failed to update row: {message}")

                # Trigger rerun to refresh the displayed data
                conditional_rerun()
            except Exception as e:
                st.error(f"Error applying changes: {e}")
