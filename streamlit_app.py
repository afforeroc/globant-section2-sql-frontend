# -*- coding: utf-8 -*-

"""
This script connects to Snowflake using the provided credentials from the .env file,
executes two SQL queries, and displays the results using Streamlit and Dash DataTables.
"""

from dotenv import dotenv_values
import snowflake.connector
from dash import dash_table
import streamlit as st


# Connect to Snowflake
def create_snowflake_connection(snowflake_credentials):
    """
    Connects to Snowflake using the provided credentials from the .env file.

    Returns:
    snowflake.connector.connection.SnowflakeConnection: A Snowflake connection object.

    Raises:
    snowflake.connector.errors.DatabaseError: If there is an error connecting to Snowflake.
    """
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
    except snowflake.connector.errors.DatabaseError as snowflake_error:
        st.error(f"Error connecting to Snowflake: {str(snowflake_error)}")
        raise


if __name__ == "__main__":
    try:
        # Load .env variables
        # snowflake_credentials = dotenv_values(".env")
        snowflake_credentials = st.secrets["snowflake_credentials"]
        
        # Snowflake connection
        ctx = create_snowflake_connection(snowflake_credentials)

        # Create a cursor object
        cur = ctx.cursor()

        # Execute a statement and fetch the result into df
        query1 = \
            """
            WITH QUERY1 AS (
                SELECT
                    HE.ID AS ID,
                    DE.DEPARTMENT AS DEPARTMENT,
                    JO.JOB AS JOB,
                    CONCAT('Q', EXTRACT(QUARTER FROM HE.DATETIME)) AS QUARTER
                FROM
                    GLOBANT_CHALLENGE_DB.RECRUITING.HIRED_EMPLOYEES HE
                    LEFT JOIN GLOBANT_CHALLENGE_DB.RECRUITING.DEPARTMENTS DE ON HE.DEPARTMENT_ID = DE.ID
                    LEFT JOIN GLOBANT_CHALLENGE_DB.RECRUITING.JOBS JO ON HE.JOB_ID = JO.ID
                WHERE
                    EXTRACT(YEAR FROM DATETIME) = 2021
            ),
            QUERY2 AS (
                SELECT
                    *
                FROM
                    QUERY1
                PIVOT (
                    COUNT(ID)
                    FOR QUARTER IN (
                        'Q1',
                        'Q2',
                        'Q3',
                        'Q4'
                    )
                ) AS PIVOT_TABLE
            )
            SELECT 
                DEPARTMENT,
                JOB,
                "'Q1'" AS Q1,
                "'Q2'" AS Q2,
                "'Q3'" AS Q3,
                "'Q4'" AS Q4
            FROM
                QUERY2
            ORDER BY 
                DEPARTMENT, JOB
            """
        cur.execute(query1)
        query1_df = cur.fetch_pandas_all()

        # Execute a statement and fetch the result into df
        query2 = \
            """
            WITH QUERY1 AS (
                SELECT
                    HE.ID AS HE_ID,
                    DE.ID AS DE_ID,
                    DE.DEPARTMENT AS DEPARTMENT
                FROM
                    GLOBANT_CHALLENGE_DB.RECRUITING.HIRED_EMPLOYEES HE
                    LEFT JOIN GLOBANT_CHALLENGE_DB.RECRUITING.DEPARTMENTS DE ON HE.DEPARTMENT_ID = DE.ID
                WHERE
                    EXTRACT(YEAR FROM DATETIME) = 2021
            ),
            QUERY2 AS (
                SELECT
                    DE_ID AS ID,
                    DEPARTMENT AS DEPARTMENT,
                    COUNT(HE_ID) AS HIRED
                FROM
                    QUERY1
                GROUP BY
                    DE_ID, DEPARTMENT
                ORDER BY COUNT(HE_ID) DESC
            )
            SELECT *
            FROM QUERY2
            WHERE HIRED > (SELECT AVG(HIRED) FROM QUERY2)
            """
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
    st.header('Requirement 1')
    st.write("Number of employees hired for each job and department in 2021 divided by quarter.")
    st.write("The table is initially ordered alphabetically by department and job.")
    # Create a Dash DataTable
    query1_dash_table = dash_table.DataTable(
        query1_df.to_dict("records")
    )
    # Display Dash DataTable in Streamlit
    st.dataframe(query1_dash_table.data)

    # Query 2
    st.header('Requirement 2')
    st.write("List of ids, name and number of employees hired of each department that hired more employees than the mean of employees hired in 2021 for all the departments.") 
    st.write("The table is initially ordered by the number of employees hired (descending).")
    # Create a Dash DataTable
    query2_dash_table = dash_table.DataTable(
        query2_df.to_dict("records")
    )
    # Display Dash DataTable in Streamlit
    st.dataframe(query2_dash_table.data)
