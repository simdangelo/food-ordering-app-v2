import streamlit as st
import pandas as pd
from common.postgres_connection import create_postgres_connection
from common.global_variables import N_RIDERS


st.set_page_config(
    page_title='Orders daily details',
    page_icon='✅',
    layout='wide'
)

# def orders_active_completed():
#     connection, cursor = create_postgres_connection()
#
#     cursor.execute("SELECT * FROM food_ordering.orders WHERE status='pending' ORDER BY order_timestamp desc;")
#     orders_pending = cursor.fetchall()
#     columns = [desc[0] for desc in cursor.description]
#     orders_pending = pd.DataFrame(orders_pending, columns=columns)
#
#     cursor.execute("SELECT * FROM food_ordering.orders WHERE status='completed' ORDER BY order_timestamp desc;")
#     orders_completed = cursor.fetchall()
#     columns = [desc[0] for desc in cursor.description]
#     orders_completed = pd.DataFrame(orders_completed, columns=columns)
#
#     connection.commit()
#     cursor.close()
#     connection.close()
#
#     return orders_pending, orders_completed

def orders_still_active(cursor):
    cursor.execute(f"""
            WITH order_status_count AS (
                SELECT 
                    order_id,
                    COUNT(DISTINCT CASE WHEN status = 'denied' THEN rider_id END) AS denied_count,
                    COUNT(DISTINCT CASE WHEN status = 'accepted' THEN rider_id END) AS accepted_count
                FROM food_ordering.orders_status
                WHERE DATE(event_timestamp) = CURRENT_DATE
                GROUP BY order_id
            )
            SELECT COUNT(DISTINCT order_id) AS active_orders
            FROM order_status_count
            WHERE accepted_count = 0 AND denied_count < {N_RIDERS};
            """)
    pending_orders = cursor.fetchone()[0]
    return pending_orders

placeholder = st.empty()

while True:
    connection, cursor = create_postgres_connection()
    with placeholder.container():
#         orders_pending, orders_completed = orders_active_completed()
#
#         col1, col2 = st.columns(2)
#         with col1:
#             st.markdown("## Active orders")
#             st.dataframe(orders_pending, use_container_width=True, hide_index=True)
#
#         with col2:
#             st.markdown("## Completed orders")
#             st.dataframe(orders_completed, use_container_width=True, hide_index=True)


        st.write("### Orders Details")
        kpi5, kpi6, kpi7, kpi8 = st.columns(4)
        with kpi5:
            kpi5.metric(label="Active orders", value=orders_still_active(cursor))
        # kpi6.metric(label="Completed orders", value=9999)
        # kpi7.metric(label="Avg Acceptance time", value=f"{average_acceptance_timestamp} min")
        # kpi8.metric(label="Avg Completion time", value=f"{average_completion_timestamp} min")

        st.divider()