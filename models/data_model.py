import streamlit as st
import pandas as pd
import os
import configparser
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session


# Establishes and caches a Snowflake session for reuse, attempting to get an active session first.
# If no active session is available, it initializes a new session using credentials from a config file.
@st.cache_resource(show_spinner="Connecting to Snowflake...")
def getSession():
    try:
        return get_active_session()  # Reuse an active session if available
    except:
        parser = configparser.ConfigParser()
        parser.read(os.path.join(os.path.expanduser("~"), ".snowsql/config"))
        section = "connections.data_eng"
        pars = {
            "account": parser.get(section, "accountname"),
            "user": parser.get(section, "username"),
            "password": parser.get(section, "password"),
        }
        return Session.builder.configs(pars).create()


# Fetches a list of distinct company names from the database, ordered alphabetically.
@st.cache_data(show_spinner="Fetching company names...")
def get_distinct_company_names():
    session = getSession()
    query = session.sql(
        """
        SELECT DISTINCT COMPANY_NAME
        FROM PRODUCTS.CUSTOMERS.MAPPING
        ORDER BY COMPANY_NAME ASC
        """
    )
    df = query.to_pandas()  # Convert result to a pandas DataFrame
    return df["COMPANY_NAME"].tolist()  # Return as a list of company names


# Fetches a list of distinct program codes for a given company, ordered alphabetically.
@st.cache_data(show_spinner="Fetching program codes...")
def get_distinct_program_codes(company):
    session = getSession()
    query = session.sql(
        """
        SELECT DISTINCT PROGRAM_CODE
        FROM PRODUCTS.CUSTOMERS.MAPPING
        WHERE COMPANY_NAME = ?
        ORDER BY PROGRAM_CODE ASC
        """,
        (company,),  # Use parameterized value for security
    )
    df = query.to_pandas()
    return df["PROGRAM_CODE"].tolist()  # Return as a list of program codes


# Fetches a list of distinct product codes for a given program, ordered alphabetically.
@st.cache_data(show_spinner="Fetching product codes...")
def get_distinct_product_codes(program_code):
    session = getSession()
    query = session.sql(
        """
        SELECT DISTINCT PRODUCT_CODE
        FROM PRODUCTS.CUSTOMERS.MAPPING
        WHERE PROGRAM_CODE = ?
        ORDER BY PRODUCT_CODE ASC
        """,
        (program_code,),  # Use parameterized value for security
    )
    df = query.to_pandas()
    return df["PRODUCT_CODE"].tolist()  # Return as a list of product codes


# Retrieves the full dataset from the specified table in Snowflake and returns it as a DataFrame.
def get_dataset(table_name):
    session = getSession()
    try:
        df = session.table(table_name).to_pandas()
        df.reset_index(inplace=True, drop=True)  # Reset index for display
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on failure


# Saves new commission data to the "COMMISSIONS" table in Snowflake.
def save_commission_data(new_commission_data):
    session = getSession()
    try:
        session.write_pandas(
            new_commission_data,
            "COMMISSIONS",
            database="PRODUCTS",
            schema="CUSTOMERS",
            overwrite=False,
        )
        return True, "Data successfully saved."
    except Exception as e:
        return False, f"Failed to save data: {e}"


# Checks if a commission entry exists in the database for the specified company, program, and product.
def check_existing_entry(company_name, program_code, product_code):
    try:
        session = getSession()
        query = session.sql(
            """
            SELECT COUNT(*)
            FROM PRODUCTS.CUSTOMERS.COMMISSIONS
            WHERE COMPANY_NAME = ? AND PROGRAM_CODE = ? AND PRODUCT_CODE = ?
            """,
            (company_name, program_code, product_code),  # Parameterized query
        )
        result = query.collect()
        record_count = result[0][0] if result else 0
        return record_count > 0  # Return True if count > 0, indicating entry exists
    except Exception as e:
        st.error(f"Error checking for existing record: {e}")
        return False


# Updates commission data for a specified company, program, and product in the database.
def update_ulr_data(
    company_name,
    program_code,
    product_code,
    commission_amount,
    is_active,
    updated_last,
    username,
):
    session = getSession()
    try:
        # Update query with placeholders for all variables
        update_query = """
        UPDATE PRODUCTS.CUSTOMERS.COMMISSIONS
        SET COMMISSION_AMOUNT = ?,
            IS_ACTIVE = ?,
            UPDATED_LAST = ?,
            USERNAME = ?
        WHERE COMPANY_NAME = ?
        AND PROGRAM_CODE = ?
        AND PRODUCT_CODE = ?
        """
        # Execute the query with parameters passed as a tuple
        session.sql(
            update_query,
            (
                commission_amount,
                is_active,
                updated_last,
                username,
                company_name,
                program_code,
                product_code,
            ),
        ).collect()

        return True, "Commission data updated successfully."
    except Exception as e:
        return False, f"Failed to update data: {e}"


# Deletes a commission entry from the database based on the specified company, program, and product.
def delete_commission_data(company_name, program_code, product_code):
    session = getSession()
    try:
        # Delete query with placeholders for all variables
        delete_query = """
        DELETE FROM PRODUCTS.CUSTOMERS.COMMISSIONS
        WHERE COMPANY_NAME = ?
        AND PROGRAM_CODE = ?
        AND PRODUCT_CODE = ?
        """
        # Execute the query with parameters passed as a tuple
        session.sql(delete_query, (company_name, program_code, product_code)).collect()

        return True, "Row deleted successfully."
    except Exception as e:
        return False, f"Failed to delete data: {e}"
