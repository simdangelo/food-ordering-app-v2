import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from common.postgres_connection import create_postgres_connection
from common.global_variables import N_RIDERS

st.set_page_config(
    page_title='Real-Time Analytics',
    page_icon='✅',
    layout='wide'
)

# dashboard title
# st.title("Real-Time Food Ordering Dashboard")

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

def calculate_daily_kpis():
    connection, cursor = create_postgres_connection()

    cursor.execute("SELECT COUNT(*) FROM food_ordering.orders_status WHERE  status='pending' and DATE(event_timestamp) = CURRENT_DATE;")
    total_orders = cursor.fetchone()[0]

    active_orders = orders_still_active(cursor)

    cursor.execute("""
            SELECT 
                sum(total_amount)
            FROM food_ordering.orders
            WHERE DATE(order_created_timestamp) = CURRENT_DATE 
        """)
    revenues = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(DISTINCT user_id)
        FROM food_ordering.users
        WHERE registration_date = CURRENT_DATE;
    """)
    new_customers = cursor.fetchone()[0]

    cursor.execute("SELECT MAX(order_created_timestamp) FROM food_ordering.orders;")
    last_order_time = cursor.fetchone()[0]

    cursor.execute("""
        SELECT 
            CAST(AVG(EXTRACT(EPOCH FROM (a.event_timestamp - b.event_timestamp)) / 60) AS INT) AS avg_minutes
        FROM food_ordering.orders_status a
        LEFT JOIN food_ordering.orders_status b ON a.order_id=b.order_id
        WHERE a.status='accepted' and b.status ='pending'
    """)
    average_acceptance_timestamp = cursor.fetchone()[0]

    # cursor.execute(
    #     "SELECT cast(avg(EXTRACT(EPOCH FROM (completion_order_timestamp - order_timestamp)) / 60) as int) FROM food_ordering.orders WHERE DATE(order_timestamp) = CURRENT_DATE;")
    # average_completion_timestamp = cursor.fetchone()[0]
    average_completion_timestamp = 9999

    connection.commit()
    cursor.close()
    connection.close()

    return total_orders, active_orders, revenues, new_customers, last_order_time, average_acceptance_timestamp, average_completion_timestamp

def food_category_ratio():
    connection, cursor = create_postgres_connection()

    cursor.execute("""
                    SELECT
                        m.category
                        , SUM(od.quantity)
                    FROM food_ordering.order_details od
                    JOIN food_ordering.menu_items m ON od.item_id = m.item_id
                    JOIN food_ordering.orders_status o ON o.order_id = od.order_id
                    WHERE m.category != 'Drink' and o.status='pending'
                    AND DATE(o.event_timestamp) = CURRENT_DATE
                    GROUP BY m.category
                """)
    results = cursor.fetchall()

    connection.commit()
    cursor.close()
    connection.close()

    return results

def drink_category_ratio():
    connection, cursor = create_postgres_connection()

    cursor.execute("""
                    SELECT
                        m.name
                        , SUM(od.quantity)
                    FROM food_ordering.order_details od
                    JOIN food_ordering.menu_items m ON od.item_id = m.item_id
                    JOIN food_ordering.orders_status o ON o.order_id = od.order_id
                    WHERE m.category = 'Drink' and o.status='pending'
                    AND DATE(o.event_timestamp) = CURRENT_DATE
                    GROUP BY m.name
                """)
    results = cursor.fetchall()

    connection.commit()
    cursor.close()
    connection.close()

    return results

def orders_by_hour():
    connection, cursor = create_postgres_connection()

    cursor.execute("""
                    SELECT
                        time_series AS time_window,
                        COUNT(orders_status.event_timestamp) AS num_orders
                    FROM
                        generate_series(
                            DATE_TRUNC('day', CURRENT_TIMESTAMP),
                            DATE_TRUNC('day', CURRENT_TIMESTAMP) + INTERVAL '1 day' - INTERVAL '1 minute',
                            INTERVAL '15 minutes'
                        ) AS time_series
                    LEFT JOIN
                        food_ordering.orders_status
                    ON
                        food_ordering.orders_status.event_timestamp >= time_series 
                        AND food_ordering.orders_status.event_timestamp < time_series + INTERVAL '15 minutes'
                        AND food_ordering.orders_status.status = 'pending'
                    GROUP BY
                        time_window
                    ORDER BY
                        time_window;
                    """)
    results = cursor.fetchall()

    connection.commit()
    cursor.close()
    connection.close()

    return results

def food_dataframe():
    connection, cursor = create_postgres_connection()

    cursor.execute("""
        SELECT
            m.category
            , SUM(od.quantity) AS quantity
            , SUM(od.subtotal) AS total_revenue
        FROM food_ordering.order_details od
        JOIN food_ordering.menu_items m ON od.item_id = m.item_id
        JOIN food_ordering.orders_status o ON o.order_id = od.order_id
        WHERE m.category != 'Drink' AND DATE(o.event_timestamp) = CURRENT_DATE
        GROUP BY m.category
        ORDER BY total_revenue DESC
    """)
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    pandas_results = pd.DataFrame(results, columns=columns)

    connection.commit()
    cursor.close()
    connection.close()

    return pandas_results

def drink_dataframe():
    connection, cursor = create_postgres_connection()

    cursor.execute("""
        SELECT
            m.name
            , SUM(od.quantity) AS quantity
            , SUM(od.subtotal) AS total_revenue
        FROM food_ordering.order_details od
        JOIN food_ordering.menu_items m ON od.item_id = m.item_id
        JOIN food_ordering.orders_status o ON o.order_id = od.order_id
        WHERE m.category = 'Drink' AND DATE(o.event_timestamp) = CURRENT_DATE
        GROUP BY m.name
        ORDER BY total_revenue DESC
    """)
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    pandas_results = pd.DataFrame(results, columns=columns)

    connection.commit()
    cursor.close()
    connection.close()

    return pandas_results


placeholder = st.empty()

while True:
    with placeholder.container():
        st.write("# Today's Analytics")

        total_orders, active_orders, revenues, new_customers, last_order_time, average_acceptance_timestamp, average_completion_timestamp = calculate_daily_kpis()

        st.write("### Orders made by Users")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric(label="Orders made today", value=total_orders)
        kpi2.metric(label="Total revenue", value=f"$ {revenues} ")
        kpi3.metric(label="New customers today", value=f"{new_customers}")
        kpi4.metric(label="Last order at", value=f"{last_order_time.strftime('%H:%M') if last_order_time else 'No orders yet'}")

        st.divider()

        st.markdown("### Orders by hour")
        results = orders_by_hour()

        data = {'hour_of_day': [], 'num_orders': []}
        for hour_of_day, num_orders in results:
            data['hour_of_day'].append(hour_of_day)
            data['num_orders'].append(num_orders)

        fig = px.bar(data, x='hour_of_day', y='num_orders')
        fig.update_layout(xaxis_tickformat='%H:%M')  # Format x-axis ticks

        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        fig_col1, fig_col2 = st.columns(2)
        with fig_col1:
            st.markdown("### Food order Details")

            results = food_category_ratio()
            df = pd.DataFrame(results, columns=['category', 'num_orders'])

            fig1 = px.pie(df, names='category', values='num_orders', title="Count of each food category")
            fig1.update_traces(textinfo='percent+label', textfont_size=14, hole=.3, textposition='auto',
                               showlegend=False)
            st.write(fig1)

            with st.expander("See details about Revenues and Quantity"):
                st.dataframe(food_dataframe(), use_container_width=True, hide_index=True)

        with fig_col2:
            st.markdown("### Drink order Details")

            results = drink_category_ratio()
            df = pd.DataFrame(results, columns=['name', 'num_orders'])

            fig2 = px.pie(df, names='name', values='num_orders', title="Count of each drink item")
            fig2.update_traces(textinfo='percent+label', textfont_size=14, hole=.3, textposition='auto',
                               showlegend=False)
            st.write(fig2)

            with st.expander("See details about Revenues and Quantity"):
                st.dataframe(drink_dataframe(), use_container_width=True, hide_index=True)