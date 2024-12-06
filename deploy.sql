-- to be deployed as a Streamlit App with: snowsql -c dev_conn -f deploy.sql
use schema DE_STREAMLIT_DEV.FINANCE;

create or replace stage stg_streamlit_finance_ulr;

put file://C:\github\streamlit\streamlit_crud\app.py @stg_streamlit_finance_ulr
    overwrite=true auto_compress=false;

put file://C:\github\streamlit\streamlit_crud\app.py @stg_streamlit_finance_ulr overwrite=true auto_compress=false;
put file://C:\github\streamlit\streamlit_crud\views\*.py @stg_streamlit_finance_ulr/views overwrite=true auto_compress=false;
put file://C:\github\streamlit\streamlit_crud\models\*.py @stg_streamlit_finance_ulr/models overwrite=true auto_compress=false;
put file://C:\github\streamlit\streamlit_crud\controllers\*.py @stg_streamlit_finance_ulr/controllers overwrite=true auto_compress=false;

create or replace streamlit finance_ulr_form
    root_location = '@DE_STREAMLIT_DEV.finance.stg_streamlit_finance_ulr'
    main_file = '/app.py'
    query_warehouse = 'WH_STREAMLIT_DEV';
    
show streamlits;
