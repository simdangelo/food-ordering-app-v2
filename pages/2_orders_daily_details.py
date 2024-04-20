import streamlit as st
import pandas as pd
from common.postgres_connection import create_postgres_connection

st.set_page_config(
    page_title='Orders daily details',
    page_icon='✅',
    layout='wide'
)

def orders_active_completed():
    connection, cursor = create_postgres_connection()

    cursor.execute("SELECT * FROM food_ordering.orders WHERE status='pending' ORDER BY order_timestamp desc;")
    orders_pending = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    orders_pending = pd.DataFrame(orders_pending, columns=columns)

    cursor.execute("SELECT * FROM food_ordering.orders WHERE status='completed' ORDER BY order_timestamp desc;")
    orders_completed = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    orders_completed = pd.DataFrame(orders_completed, columns=columns)

    connection.commit()
    cursor.close()
    connection.close()

    return orders_pending, orders_completed


placeholder = st.empty()

while True:
    with placeholder.container():
        orders_pending, orders_completed = orders_active_completed()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("## Active orders")
            st.dataframe(orders_pending, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("## Completed orders")
            st.dataframe(orders_completed, use_container_width=True, hide_index=True)
