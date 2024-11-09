import streamlit as st
import time


# Function to set the Streamlit page layout to wide mode
def set_page_config():
    st.set_page_config(layout="wide")


# Function to display a header title for the page
def display_title(title_text):
    st.header(title_text)


# Function to display a select box (dropdown) with given label, options, and unique key
def display_selectbox(label, options, key):
    return st.selectbox(label, options=options, key=key)


# Function to display a number input field with specified label, key, and minimum value
def display_number_input(label, key, min_value=0.0):
    return st.number_input(label, key=key, min_value=min_value)


# Function to create a submit button within a form, with a unique form key
def display_form_submit_button(label, form_key=""):
    with st.form(key=form_key, clear_on_submit=True):
        return st.form_submit_button(label)


# Function to display an error message for a specified duration, then clear it
def display_error_message(message):
    duration = 5  # Duration in seconds to show the error message
    placeholder = st.empty()  # Create a temporary placeholder
    placeholder.error(f"🔴 {message}")  # Display the error message with an icon
    time.sleep(duration)  # Wait for the specified duration
    placeholder.empty()  # Clear the message after duration


# Function to display a success message for a specified duration, then clear it
def display_success_message(message):
    duration = 3  # Duration in seconds to show the success message
    placeholder = st.empty()  # Create a temporary placeholder
    placeholder.success(f"✅ {message}")  # Display the success message with an icon
    time.sleep(duration)  # Wait for the specified duration
    placeholder.empty()  # Clear the message after duration
