import streamlit as st
from controllers import app_controller as controller
import views.app_view as view


# Main function to run the Streamlit application
def main():
    # Set page to wide layout for optimal screen space usage
    view.set_page_config()

    # Display the main title of the application
    view.display_title("Customer Commission Ratio")

    # Initialize session state variables at the very start to manage app state
    controller.initialize_session_state()

    # Display dropdown for selecting a company
    controller.get_company_selection()

    # Display dropdown for selecting a program based on selected company
    controller.get_program_selection()

    # Display multiselect for selecting products based on selected program
    controller.get_product_selection()

    # Display input field for entering the commission amount
    controller.get_commission_input()

    # Handle form submission, which includes validation and saving data
    controller.handle_form_submission()

    # Display the commission table at the bottom of the page with filtering options
    controller.display_commission_table()


# Entry point to run the main function when the script is executed
if __name__ == "__main__":
    main()
