import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from common.postgres_connection import create_postgres_connection

st.set_page_config(
    page_title='Riders Details',
    layout='wide'
)

def riders_list():
    connection, cursor = create_postgres_connection()
    cursor.execute("SELECT COUNT(DISTINCT(rider_id)) FROM food_ordering.riders")
    n_riders = cursor.fetchone()[0]

    connection.commit()
    cursor.close()
    connection.close()

    return n_riders

def n_riders():
    connection, cursor = create_postgres_connection()
    cursor.execute("SELECT COUNT(DISTINCT(rider_id)) FROM food_ordering.riders")
    n_riders = cursor.fetchone()[0]

    connection.commit()
    cursor.close()
    connection.close()

    return n_riders

def orders_by_riders_status():
    connection, cursor = create_postgres_connection()
    cursor.execute("""
            SELECT
                a.name,
                b.status,
                count(b.order_id)
            FROM food_ordering.riders a
            LEFT JOIN food_ordering.orders_status b on a.rider_id=b.rider_id
            GROUP BY a.name, b.status
            ORDER BY a.name, b.status
        """)
    orders_by_riders_status = cursor.fetchall()

    connection.commit()
    cursor.close()
    connection.close()

    return orders_by_riders_status

def main():

    st.write("# Riders Details")

    st.write("### Aggregate Analytics")

    results = orders_by_riders_status()
    print(results)
    data = {'rider_name': [], 'status': [], 'count': []}
    for rider_name, status, count in results:
        data['rider_name'].append(rider_name)
        data['status'].append(status)
        data['count'].append(count)
    print(data)
    fig = px.bar(data, x='rider_name', y='count', color='status', barmode='group')
    # fig.update_layout(title='Completed Orders by Riders')
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()