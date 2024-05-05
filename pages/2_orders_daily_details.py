import streamlit as st
import pandas as pd
from common.postgres_connection import create_postgres_connection
from common.global_variables import N_RIDERS


st.set_page_config(
    page_title='Orders daily details',
    page_icon='✅',
    layout='wide'
)

def total_orders(cursor):
    cursor.execute(
        "SELECT COUNT(*) FROM food_ordering.orders_status WHERE status='pending' and DATE(event_timestamp) = CURRENT_DATE;")
    total_orders = cursor.fetchone()[0]

    return total_orders

def pending_orders(cursor):
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

def accepted_orders(cursor):
    cursor.execute(f"""
            SELECT COUNT(*) FROM food_ordering.orders_status WHERE status = 'accepted' AND DATE(event_timestamp) = CURRENT_DATE
            """)
    orders_accepted = cursor.fetchone()[0]
    return orders_accepted

def denied_orders(cursor):
    cursor.execute(f"""
        WITH TMP AS (
            SELECT COUNT(status)
            FROM food_ordering.orders_status
            WHERE status = 'denied' AND DATE(event_timestamp) = CURRENT_DATE
            GROUP BY order_id
            HAVING COUNT(status) = {N_RIDERS}
        )
        SELECT COUNT(*)
        FROM TMP
    """)
    denied_orders = cursor.fetchone()[0]
    return denied_orders

def completed_orders(cursor):
    cursor.execute(f"""
        SELECT COUNT(status) FROM food_ordering.orders_status WHERE status = 'completed' AND DATE(event_timestamp) = CURRENT_DATE
    """)
    completed_orders = cursor.fetchone()[0]
    return completed_orders


def average_acceptance_timestamp():
    cursor.execute(f"""
            SELECT
                avg(a.event_timestamp - b.event_timestamp)
            FROM food_ordering.orders_status a
            LEFT JOIN food_ordering.orders_status b on a.order_id=b.order_id
            WHERE a.status = 'accepted' and b.status = 'pending' AND DATE(a.event_timestamp) = CURRENT_DATE
        """)
    average_acceptance_timedelta = cursor.fetchone()[0]
    average_acceptance_seconds = average_acceptance_timedelta.total_seconds() if average_acceptance_timedelta else 0

    minutes = int(average_acceptance_seconds // 60)
    seconds = int(average_acceptance_seconds % 60)

    formatted_average_acceptance_timestamp = f"{minutes}'{seconds}''"

    return formatted_average_acceptance_timestamp

def average_completion_timestamp():
    cursor.execute(f"""
            SELECT
                avg(a.event_timestamp - b.event_timestamp)
            FROM food_ordering.orders_status a
            LEFT JOIN food_ordering.orders_status b on a.order_id=b.order_id
            WHERE a.status = 'completed' and b.status = 'pending' AND DATE(a.event_timestamp) = CURRENT_DATE
        """)
    average_completion_timedelta = cursor.fetchone()[0]
    average_completion_seconds = average_completion_timedelta.total_seconds() if average_completion_timedelta else 0

    minutes = int(average_completion_seconds // 60)
    seconds = int(average_completion_seconds % 60)

    formatted_average_completion_seconds = f"{minutes}'{seconds}''"

    return formatted_average_completion_seconds


placeholder = st.empty()

while True:
    connection, cursor = create_postgres_connection()
    with placeholder.container():
        st.write("### Orders Details")
        st.write("**Pending**: riders are still deciding what to do with these orders. This order can be still accepted by one rider or denied by all riders.")
        st.write("**Accepted**: one of the riders has accepted this order.")
        st.write("**Denied**: all riders has denied this order.")
        st.write("**Completed**: after acceptance, the rider has delivered this order.")
        st.write("**Succesful rate**: ratio between Completed orders and Total orders.")

        st.divider()

        kpi5, kpi6, kpi7, kpi8, kpi9, kpi10 = st.columns(6)
        kpi5.metric(label="Total orders", value=total_orders(cursor))
        kpi6.metric(label="Pending orders", value=pending_orders(cursor))
        kpi7.metric(label="Accepted orders", value=accepted_orders(cursor))
        kpi8.metric(label="Denied orders", value=denied_orders(cursor))
        kpi9.metric(label="Completed orders", value=completed_orders(cursor))
        success_rate = round(completed_orders(cursor) / total_orders(cursor) * 100, 2) if total_orders(cursor) != 0 else 0
        kpi10.metric(label="Successful rate", value=f"{success_rate}%")

        st.divider()

        kpi11, kpi12 = st.columns(2)
        kpi11.metric(label="Avg Acceptance time", value=f"{average_acceptance_timestamp()}")
        kpi12.metric(label="Avg Completion time", value=f"{average_completion_timestamp()}")