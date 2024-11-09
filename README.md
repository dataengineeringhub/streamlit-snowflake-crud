
# Customer Commission Ratio Management App

This repository contains the source code for a Streamlit application that manages customer commission ratios with Snowflake as the backend. This app allows users to select company, program, and product codes, set commission amounts, and manage data directly in Snowflake. The repository is part of a YouTube tutorial series on data engineering, where we build and deploy this app step-by-step.

## Overview

- **App Features**:
  - Selection and entry of company, program, and product codes.
  - In-place data entry for commission amounts with validation.
  - Display and editing of commission data stored in Snowflake.
  - Filtering, sorting, and bulk approval of data records.
- **Backend**: Powered by Snowflake for data storage and retrieval.
- **Frontend**: Developed in Python using the Streamlit framework.

## Table of Contents

1. [Requirements](#requirements)
2. [Setup](#setup)
3. [Usage](#usage)
4. [Application Structure](#application-structure)
5. [Database Schema](#database-schema)
6. [Features](#features)
7. [FAQ](#faq)
8. [Contact and Support](#contact-and-support)

---

## Requirements

- **Python**: Version 3.8+
- **Snowflake**: Active account with permissions to create tables and manage data
- **Streamlit**: Version 1.35.0 (required for Snowflake integration)

### Required Python Libraries

Install the necessary libraries with:

```bash
pip install -r requirements.txt
```

**Requirements File Contents**:
- Streamlit
- Snowflake Connector
- Pandas
- Configparser (for reading config files)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YourGitHubUsername/customer-commission-app.git
cd customer-commission-app
```

### 2. Configure Snowflake Connection

Set up a Snowflake connection file:
1. **File**: `.snowsql/config`
2. **Section**: `[connections.data_eng]`
3. **Settings**: `accountname`, `username`, `password`

You can follow the guide on setting up Snowflake connections in the official [Snowflake Documentation](https://docs.snowflake.com/).

### 3. Database Setup

Use the provided `db-setup.sql` and `deploy.sql` files to create and deploy the necessary schema and tables in your Snowflake environment.

1. Execute `db-setup.sql` to initialize the database structure.
2. Execute `deploy.sql` for any deployment-specific configurations.

```bash
# Example command to execute SQL files (adjust to your preferred method)
snowsql -a <account> -u <username> -p <password> -f db-setup.sql
snowsql -a <account> -u <username> -p <password> -f deploy.sql
```

### 4. Run the Application

To start the Streamlit app:

```bash
streamlit run app.py
```

## Usage

Follow the steps to use the app:
1. **Company Selection**: Select a company from the dropdown.
2. **Program Selection**: Choose a program associated with the selected company.
3. **Product Selection**: Select the products.
4. **Commission Entry**: Enter a commission amount and submit.

Changes are stored in Snowflake and can be edited or deleted as required.

## Application Structure

- `app.py`: Main file to run the app.
- `app_view.py`: Manages the visual aspects of the app.
- `data_model.py`: Handles data operations, connecting to Snowflake.
- `app_controller.py`: Manages app logic, including state handling and data flow.
- `db-setup.sql` & `deploy.sql`: SQL scripts for initial setup and deployment.

## Database Schema

The database contains the following key tables:

### COMMISSIONS Table

| Column          | Type        | Description                                 |
|-----------------|-------------|---------------------------------------------|
| COMPANY_NAME    | VARCHAR     | Name of the company                         |
| PROGRAM_CODE    | VARCHAR     | Code representing the program               |
| PRODUCT_CODE    | VARCHAR     | Code for the specific product               |
| COMMISSION_AMOUNT | FLOAT     | Assigned commission amount                  |
| IS_ACTIVE       | BOOLEAN     | Indicates if the commission is active       |
| UPDATED_LAST    | DATETIME    | Timestamp of the last update                |
| USERNAME        | VARCHAR     | User who last updated the record            |

For more details, see the `db-setup.sql` file.

## Features

### Data Entry & Management

- **Company, Program, Product Selection**: Filterable dropdowns for data selection.
- **Commission Entry**: Number input field with validation.
- **Data Editing**: Modify and delete entries directly in the table.

### Data Filters

- **Sidebar Filters**: Filter by company, program, and product codes.
- **Date Range**: Filter by date to view specific data entries.

### Bulk Approval

Select multiple entries for approval in bulk, with a single approval button.

## FAQ

### What if I encounter an error while connecting to Snowflake?
Ensure the `.snowsql/config` file is properly set up with correct permissions. Check Snowflake connection settings in the [documentation](https://docs.snowflake.com/).

### How can I deploy this app?
You can deploy this app on any platform that supports Streamlit and Snowflake connections. Options include [Streamlit Cloud](https://streamlit.io/cloud), AWS, or Heroku.

## Contact and Support

For issues, feel free to open a GitHub issue or reach out through the comments on the YouTube video.

---
