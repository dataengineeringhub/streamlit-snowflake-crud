import streamlit as st
import pandas as pd
import os
import configparser
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session


@st.cache_resource(show_spinner="Connecting to Snowflake...")
def getSession():
    try:
        return get_active_session()
    except:
        parser = configparser.ConfigParser()
        parser.read(os.path.join(os.path.expanduser("~"), ".snowsql/config"))
        section = "connections.dev_conn"
        pars = {
            "account": parser.get(section, "accountname"),
            "user": parser.get(section, "username"),
            "password": parser.get(section, "password"),
        }
        return Session.builder.configs(pars).create()


@st.cache_data(show_spinner="Fetching producer names...")
def get_distinct_producer_names():
    session = getSession()
    query = session.sql(
        """
        SELECT DISTINCT PRODUCER_NAME
        FROM SPECIALTY_DEV.ODS.ODS_IMS_PREMIUM_CLAIM_MONTH_END_FINANCE
        ORDER BY PRODUCER_NAME ASC
        """
    )
    df = query.to_pandas()
    return df["PRODUCER_NAME"].tolist()


@st.cache_data(show_spinner="Fetching program codes...")
def get_distinct_program_codes(producer):
    session = getSession()
    query = session.sql(
        """
        SELECT DISTINCT PROGRAM_CODE
        FROM SPECIALTY_DEV.ODS.ODS_IMS_PREMIUM_CLAIM_MONTH_END_FINANCE
        WHERE PRODUCER_NAME = ?
        ORDER BY PROGRAM_CODE ASC
        """,
        (producer,),  # Parameterized value as a tuple
    )
    df = query.to_pandas()
    return df["PROGRAM_CODE"].tolist()


@st.cache_data(show_spinner="Fetching product codes...")
def get_distinct_product_codes(program_code):
    session = getSession()
    query = session.sql(
        """
        SELECT DISTINCT PRODUCT_CODE
        FROM SPECIALTY_DEV.ODS.ODS_IMS_PREMIUM_CLAIM_MONTH_END_FINANCE
        WHERE PROGRAM_CODE = ?
        ORDER BY PRODUCT_CODE ASC
        """,
        (program_code,),  # Parameterized value as a tuple
    )
    df = query.to_pandas()
    return df["PRODUCT_CODE"].tolist()


def get_dataset(table_name):
    session = getSession()
    try:
        df = session.table(table_name).to_pandas()
        df.reset_index(inplace=True, drop=True)
        # st.write("Debugging - Retrieved Data:", df)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame as a fallback


def save_ulr_data(new_ulr_data):
    session = getSession()
    try:
        session.write_pandas(
            new_ulr_data,
            "ULTIMATE_LOSS_RATIO",
            database="DE_STREAMLIT_DEV",
            schema="FINANCE",
            overwrite=False,
        )
        return True, "Data successfully saved."
    except Exception as e:
        return False, f"Failed to save data: {e}"


def check_existing_entry(producer_name, program_code, product_code):
    try:
        session = getSession()
        query = session.sql(
            """
            SELECT COUNT(*)
            FROM DE_STREAMLIT_DEV.FINANCE.ULTIMATE_LOSS_RATIO
            WHERE PRODUCER_NAME = ? AND PROGRAM_CODE = ? AND PRODUCT_CODE = ?
            """,
            (producer_name, program_code, product_code),
        )
        result = query.collect()
        record_count = result[0][0] if result else 0
        return record_count > 0
    except Exception as e:
        st.error(f"Error checking for existing record: {e}")
        return False


def update_ulr_data(
    producer_name,
    program_code,
    product_code,
    ultimate_loss_ratio,
    is_active,
    updated_last,
    username,
):
    session = getSession()
    try:
        # Use parameterized query with placeholders for all variables
        update_query = """
        UPDATE DE_STREAMLIT_DEV.FINANCE.ULTIMATE_LOSS_RATIO
        SET ULTIMATE_LOSS_RATIO = ?,
            IS_ACTIVE = ?,
            UPDATED_LAST = ?,
            USERNAME = ?
        WHERE PRODUCER_NAME = ?
        AND PROGRAM_CODE = ?
        AND PRODUCT_CODE = ?
        """

        # Execute the query with parameters passed as a tuple
        session.sql(
            update_query,
            (
                ultimate_loss_ratio,
                is_active,
                updated_last,
                username,
                producer_name,
                program_code,
                product_code,
            ),
        ).collect()

        return True, "ULR data updated successfully."
    except Exception as e:
        return False, f"Failed to update data: {e}"


def delete_ulr_data(producer_name, program_code, product_code):
    session = getSession()
    try:
        # Parameterized query with placeholders for all variables
        delete_query = """
        DELETE FROM DE_STREAMLIT_DEV.FINANCE.ULTIMATE_LOSS_RATIO
        WHERE PRODUCER_NAME = ?
        AND PROGRAM_CODE = ?
        AND PRODUCT_CODE = ?
        """

        # Execute the query with parameters passed as a tuple
        session.sql(delete_query, (producer_name, program_code, product_code)).collect()

        return True, "Row deleted successfully."
    except Exception as e:
        return False, f"Failed to delete data: {e}"
