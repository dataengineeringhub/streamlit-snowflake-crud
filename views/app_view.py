import streamlit as st
import time


def set_page_config():
    st.set_page_config(layout="wide")


def display_title(title_text):
    st.header(title_text)


def display_selectbox(label, options, key):
    return st.selectbox(label, options=options, key=key)


def display_number_input(label, key, min_value=0.0):
    return st.number_input(label, key=key, min_value=min_value)


def display_form_submit_button(label, form_key=""):
    with st.form(key=form_key, clear_on_submit=True):
        return st.form_submit_button(label)


def display_error_message(message):
    duration = 5
    placeholder = st.empty()
    placeholder.error(f"🔴 {message}")
    time.sleep(duration)
    placeholder.empty()


def display_success_message(message):
    duration = 3
    placeholder = st.empty()
    placeholder.success(f"✅ {message}")
    time.sleep(duration)
    placeholder.empty()
