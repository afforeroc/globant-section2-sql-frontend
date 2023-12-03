# -*- coding: utf-8 -*-

from dotenv import dotenv_values
import pandas as pd
import snowflake.connector
import streamlit as st
from dash import dash_table

# Load JSON data from the .env file
snowflake_credentials = dotenv_values(".env")

# Connect to Snowflake
def create_snowflake_connection():
    try:
        snowflake_connection = snowflake.connector.connect(
            user=snowflake_credentials["user_login"],
            password=snowflake_credentials["password"],
            account=snowflake_credentials["account"],
            warehouse=snowflake_credentials["warehouse"],
            database=snowflake_credentials["database"],
            schema=snowflake_credentials["schema"]
        )
        return snowflake_connection
    except snowflake.connector.errors.DatabaseError as e:
        st.error(f"Error connecting to Snowflake: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Snowflake connection
        ctx = create_snowflake_connection()

        # Create a cursor object.
        cur = ctx.cursor()

        # Execute a statement and fetch the result into df
        query1 = "select * from jobs"
        cur.execute(query1)
        query1_df = cur.fetch_pandas_all()

        # Execute a statement and fetch the result into df
        query2 = "select * from departments"
        cur.execute(query2)
        query2_df = cur.fetch_pandas_all()

    except snowflake.connector.errors.ProgrammingError as e:
        st.error(f"Error executing Snowflake query: {str(e)}")
        raise

    finally:
        # Always close the Snowflake connection in a finally block
        if 'ctx' in locals() and ctx is not None:
            ctx.close()

    # Page setup
    st.title("Stakeholder's Dashboard")

    # Query 1
    st.header('Query 1')
    # Create a Dash DataTable
    query1_dash_table = dash_table.DataTable(
        query1_df.to_dict("records")
    )
    # Display Dash DataTable in Streamlit
    st.dataframe(query1_dash_table.data)

    # Query 2
    st.header('Query 2')
    # Create a Dash DataTable
    query2_dash_table = dash_table.DataTable(
        query2_df.to_dict("records")
    )
    # Display Dash DataTable in Streamlit
    st.dataframe(query2_dash_table.data)
