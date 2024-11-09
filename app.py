import streamlit as st
from controllers import app_controller as controller
import views.app_view as view


def main():
    # Set page to wide layout
    view.set_page_config()

    view.display_title("Customer Commission Ratio")

    # Initialize session state variables at the very start
    controller.initialize_session_state()

    # Display producer selection
    controller.get_company_selection()

    # Display program selection
    controller.get_program_selection()

    # Display product selection
    controller.get_product_selection()

    # Display commission input
    controller.get_commission_input()

    # Handle form submission
    controller.handle_form_submission()

    # Display the commission table at the bottom
    controller.display_commission_table()


if __name__ == "__main__":
    main()
