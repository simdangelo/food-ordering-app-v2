import streamlit as st
import pandas as pd
from common.postgres_connection import create_postgres_connection
import plotly.graph_objects as go
import os

import plotly.express as px
import json


st.set_page_config(
    page_title='Orders daily details',
    page_icon='✅',
    layout='wide'
)


def yearly_orders(selected_year):
    connection, cursor = create_postgres_connection()

    cursor.execute("""
                        SELECT
                            EXTRACT(MONTH FROM event_timestamp) AS month,
                            COUNT(*) AS num_orders
                        FROM food_ordering.orders_status
                        WHERE status='pending' and EXTRACT(YEAR FROM event_timestamp) = %s
                        GROUP BY
                            EXTRACT(MONTH FROM event_timestamp)
                        ORDER BY
                            month;
                        """, (selected_year,))
    results = cursor.fetchall()

    connection.commit()
    cursor.close()
    connection.close()

    return results


def yearly_revenues(selected_year):
    connection, cursor = create_postgres_connection()

    cursor.execute("""
                    SELECT
                        EXTRACT(MONTH FROM a.event_timestamp) AS month,
                        SUM(b.total_amount) AS num_orders
                    FROM food_ordering.orders_status a
                    LEFT JOIN food_ordering.orders b
                    ON a.order_id = b.order_id
                    WHERE
                        a.status='pending' AND 
                        EXTRACT(YEAR FROM a.event_timestamp) = %s
                    GROUP BY
                        EXTRACT(MONTH FROM a.event_timestamp)
                    """, (selected_year,))
    results = cursor.fetchall()

    connection.commit()
    cursor.close()
    connection.close()

    return results

def region_orders(selected_year):
    connection, cursor = create_postgres_connection()

    cursor.execute("""
                    SELECT
                        EXTRACT(MONTH FROM event_timestamp) AS month,
                        delivery_city,
                        COUNT(*) AS num_orders
                    FROM food_ordering.orders_status
                        WHERE EXTRACT(YEAR FROM event_timestamp) = %s
                    GROUP BY
                        EXTRACT(MONTH FROM event_timestamp),
                        delivery_city
                    ORDER BY
                        month;
                    """, (selected_year,))
    results = cursor.fetchall()

    connection.commit()
    cursor.close()
    connection.close()

    return results


def calculate_min_max_year():
    connection, cursor = create_postgres_connection()

    cursor.execute("""
                    SELECT
                        EXTRACT(YEAR FROM MIN(event_timestamp)),
                        EXTRACT(YEAR FROM MAX(event_timestamp))
                    FROM food_ordering.orders_status
                        WHERE status='pending'
                    """)
    results = cursor.fetchone()

    return results


def main():

    min_year, max_year = calculate_min_max_year()

    # Generate unique keys for the selectboxes
    selected_year = st.selectbox("Select Year", list(range(int(min_year), int(max_year) + 1)), index=int(max_year) - int(min_year))

    # Orders data
    results_orders = yearly_orders(selected_year)
    chart_data_orders = pd.DataFrame(results_orders, columns=['Month', 'Num_Orders'])
    chart_data_orders['Month'] = chart_data_orders['Month'].astype(float)
    chart_data_orders['Num_Orders'] = chart_data_orders['Num_Orders'].astype(float)

    # Revenues data
    results_revenues = yearly_revenues(selected_year)
    chart_data_revenues = pd.DataFrame(results_revenues, columns=['Month', 'Revenues'])
    chart_data_revenues['Month'] = chart_data_revenues['Month'].astype(float)
    chart_data_revenues['Revenues'] = chart_data_revenues['Revenues'].astype(float)

    # Calculate y-axis limits
    orders_max = chart_data_orders['Num_Orders'].max() * 1.1  # 10% more than the maximum value
    revenues_max = chart_data_revenues['Revenues'].max() * 1.1  # 10% more than the maximum value

    # Create figure
    fig = go.Figure()

    # Add bar trace for Number of Orders
    fig.add_trace(go.Bar(x=chart_data_orders['Month'], y=chart_data_orders['Num_Orders'], name='Number of Orders'))

    # Add line trace for Revenues with secondary y-axis
    fig.add_trace(
        go.Scatter(x=chart_data_revenues['Month'], y=chart_data_revenues['Revenues'], mode='lines', name='Revenues',
                   yaxis='y2', line=dict(color='red')))

    # Update layout
    fig.update_layout(
        title='Yearly Orders and Revenues',
        xaxis=dict(title='Month', range=[0.5, 12.5], dtick=1),
        yaxis=dict(title='Number of Orders', range=[0, orders_max]),
        yaxis2=dict(title='Revenues', range=[0, revenues_max], overlaying='y', side='right')
    )

    st.plotly_chart(fig, use_container_width=True)



if __name__ == "__main__":
    main()