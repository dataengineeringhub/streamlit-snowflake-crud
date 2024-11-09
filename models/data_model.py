import streamlit as st
import pandas as pd
import os
import configparser
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session


# Establishes and caches a Snowflake session for reuse. It attempts to use an existing
# active session first. If no active session is available, it initializes a new session
# using credentials from a configuration file.
@st.cache_resource(show_spinner="Connecting to Snowflake...")
def getSession():
    try:
        # Attempt to get and reuse an existing active Snowflake session
        return get_active_session()  # Reuse an active session if available
    except:
        # If no active session, set up a new session using credentials from a local config file
        parser = configparser.ConfigParser()

        # Read Snowflake credentials from the ".snowsql/config" file in the user's home directory
        parser.read(os.path.join(os.path.expanduser("~"), ".snowsql/config"))

        # Specify configuration section to read connection details for the "data_eng" connection
        section = "connections.data_eng"

        # Retrieve account, username, and password from the config file and store in a dictionary
        pars = {
            "account": parser.get(section, "accountname"),
            "user": parser.get(section, "username"),
            "password": parser.get(section, "password"),
        }

        # Create a new Snowflake session using the configuration details
        return Session.builder.configs(pars).create()


# Function to fetch a list of distinct company names from the database, ordered alphabetically
@st.cache_data(show_spinner="Fetching company names...")
def get_distinct_company_names():
    # Get a Snowflake session to execute the query
    session = getSession()

    # Define and execute SQL query to select distinct company names from specified database table
    query = session.sql(
        """
        SELECT DISTINCT COMPANY_NAME
        FROM PRODUCTS.CUSTOMERS.MAPPING
        ORDER BY COMPANY_NAME ASC
        """
    )

    # Convert the query result to a pandas DataFrame for easy data manipulation
    df = query.to_pandas()

    # Return the 'COMPANY_NAME' column as a list of company names
    return df["COMPANY_NAME"].tolist()


# Function to fetch a list of distinct program codes for a specified company, ordered alphabetically
@st.cache_data(show_spinner="Fetching program codes...")
def get_distinct_program_codes(company):
    # Get a Snowflake session to execute the query
    session = getSession()

    # Define and execute a SQL query to select distinct program codes for the given company
    # Parameterized query is used to prevent SQL injection by binding the company parameter
    query = session.sql(
        """
        SELECT DISTINCT PROGRAM_CODE
        FROM PRODUCTS.CUSTOMERS.MAPPING
        WHERE COMPANY_NAME = ?
        ORDER BY PROGRAM_CODE ASC
        """,
        (
            company,
        ),  # Pass company as a parameter tuple to ensure safe and accurate filtering
    )

    # Convert the query result to a pandas DataFrame for easy data manipulation
    df = query.to_pandas()

    # Return the 'PROGRAM_CODE' column as a list of program codes
    return df["PROGRAM_CODE"].tolist()


# Function to fetch a list of distinct product codes for a specified program, ordered alphabetically
@st.cache_data(show_spinner="Fetching product codes...")
def get_distinct_product_codes(program_code):
    # Get a Snowflake session to execute the query
    session = getSession()

    # Define and execute a SQL query to select distinct product codes for the given program code
    # Parameterized query to prevent SQL injection by securely binding the program_code parameter
    query = session.sql(
        """
        SELECT DISTINCT PRODUCT_CODE
        FROM PRODUCTS.CUSTOMERS.MAPPING
        WHERE PROGRAM_CODE = ?
        ORDER BY PRODUCT_CODE ASC
        """,
        (
            program_code,
        ),  # Pass program_code as a parameter tuple to ensure safe filtering
    )

    # Convert the query result to a pandas DataFrame for easy data manipulation
    df = query.to_pandas()

    # Return the 'PRODUCT_CODE' column as a list of product codes
    return df["PRODUCT_CODE"].tolist()


# Function to retrieve full dataset from specified table in Snowflake
# and return it as a pandas DataFrame
def get_dataset(table_name):
    # Get a Snowflake session to execute the query
    session = getSession()
    try:
        # Fetch the specified table from Snowflake and convert the to a pandas DataFrame
        df = session.table(table_name).to_pandas()

        # Reset the index of the DataFrame, dropping the old index to ensure a clean display
        df.reset_index(inplace=True, drop=True)

        # Return the DataFrame containing the full dataset
        return df
    except Exception as e:
        # Display an error message in the Streamlit app if there’s an issue fetching the data
        st.error(f"Error fetching data: {e}")

        # Return an empty DataFrame as a fallback in case of an error
        return pd.DataFrame()


# Function to save new commission data to the "COMMISSIONS" table in Snowflake
def save_commission_data(new_commission_data):
    # Get a Snowflake session to execute the data save operation
    session = getSession()
    try:
        # Write the provided pandas DataFrame to the specified table in Snowflake
        session.write_pandas(
            new_commission_data,  # DataFrame containing the new commission data
            "COMMISSIONS",  # Target table name in Snowflake
            database="PRODUCTS",  # Target database in Snowflake
            schema="CUSTOMERS",  # Target schema within the database
            overwrite=False,  # Append to the table without overwriting existing data
        )
        # Return a success status and message if data is saved successfully
        return True, "Data successfully saved."
    except Exception as e:
        # Return a failure status and error message if an exception occurs during the save operation
        return False, f"Failed to save data: {e}"


# Function to check if a commission entry exists for a specific company, program, and product
def check_existing_entry(company_name, program_code, product_code):
    try:
        # Get a Snowflake session to execute the query
        session = getSession()

        # Define and execute a SQL query to count records matching the specified
        # company, program, and product
        # The query is parameterized to prevent SQL injection, using placeholders for inputs
        query = session.sql(
            """
            SELECT COUNT(*)
            FROM PRODUCTS.CUSTOMERS.COMMISSIONS
            WHERE COMPANY_NAME = ? AND PROGRAM_CODE = ? AND PRODUCT_CODE = ?
            """,
            (
                company_name,
                program_code,
                product_code,
            ),  # Pass parameters securely as a tuple
        )

        # Execute the query and collect the result
        result = query.collect()

        # Extract the count from the result; if result is empty, default count to 0
        record_count = result[0][0] if result else 0

        # Return True if the count is greater than 0, indicating an entry exists;
        # otherwise, return False
        return record_count > 0
    except Exception as e:
        # Display an error message in the Streamlit app if there’s an issue checking the record
        st.error(f"Error checking for existing record: {e}")

        # Return False to indicate no entry found in case of an error
        return False


# Function to update commission data for a specified company, program, and product in the database
def update_ulr_data(
    company_name,
    program_code,
    product_code,
    commission_amount,
    is_active,
    updated_last,
    username,
):
    # Get a Snowflake session to execute the update query
    session = getSession()
    try:
        # Define an update query with placeholders for the variables to prevent SQL injection
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

        # Execute the update query, passing all parameters as a tuple in the correct order
        session.sql(
            update_query,
            (
                commission_amount,  # New commission amount to set
                is_active,  # New active status
                updated_last,  # Timestamp for the last update
                username,  # Username of the person making the update
                company_name,  # Filters: company name for the entry to update
                program_code,  # Filters: program code for the entry to update
                product_code,  # Filters: product code for the entry to update
            ),
        ).collect()  # Execute the query and collect the result to complete the update operation

        # Return success status and message if the update completes without errors
        return True, "Commission data updated successfully."
    except Exception as e:
        # Return failure status and an error message if an exception occurs during the update
        return False, f"Failed to update data: {e}"


# Function to delete a commission entry from the database based on specified company,
# program, and product identifiers
def delete_commission_data(company_name, program_code, product_code):
    # Get a Snowflake session to execute the delete query
    session = getSession()
    try:
        # Define a delete query with placeholders to securely insert variables
        delete_query = """
        DELETE FROM PRODUCTS.CUSTOMERS.COMMISSIONS
        WHERE COMPANY_NAME = ?
        AND PROGRAM_CODE = ?
        AND PRODUCT_CODE = ?
        """

        # Execute the delete query, passing company, program, and product as parameters in a tuple
        session.sql(delete_query, (company_name, program_code, product_code)).collect()

        # Return a success status and message if the delete operation completes successfully
        return True, "Row deleted successfully."
    except Exception as e:
        # Return a failure status and error message if an exception occurs during deletion
        return False, f"Failed to delete data: {e}"
