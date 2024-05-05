import streamlit as st
import pandas as pd
import plotly.express as px
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
                status_values.status,
                COUNT(b.order_id) AS count_orders
            FROM food_ordering.riders a
            CROSS JOIN (
                SELECT 'accepted' AS status UNION ALL
                SELECT 'denied' UNION ALL
                SELECT 'completed'
            ) AS status_values
            LEFT JOIN food_ordering.orders_status b ON a.rider_id = b.rider_id AND b.status = status_values.status  AND DATE(b.event_timestamp) = CURRENT_DATE
            GROUP BY a.name, status_values.status
            ORDER BY a.name, status_values.status;
        """)
    orders_by_riders_status = cursor.fetchall()

    connection.commit()
    cursor.close()
    connection.close()

    return orders_by_riders_status

def riders_list():
    connection, cursor = create_postgres_connection()
    cursor.execute("""
                SELECT rider_id, name FROM food_ordering.riders
            """)
    riders_list = cursor.fetchall()

    connection.commit()
    cursor.close()
    connection.close()

    return riders_list


def monthly_rider_information(selected_rider, start_date, end_date):
    connection, cursor = create_postgres_connection()
    cursor.execute("""
                    SELECT
                        time_series AS time_window,
                        COUNT(CASE WHEN b.status = 'completed' THEN 1 END) AS completed_order_count,
                        COUNT(CASE WHEN b.status = 'denied' THEN 1 END) AS denied_order_count
                    FROM
                        generate_series(
                            %(start_date)s::DATE,
                            %(end_date)s::DATE,
                            INTERVAL '1 day'
                        ) AS time_series
                    LEFT JOIN food_ordering.orders_status AS b
                    ON b.event_timestamp::DATE = time_series::DATE
                    AND b.rider_id = %(rider_id)s
                    GROUP BY time_window
                    ORDER BY time_window;
            """, {'rider_id': selected_rider, 'start_date': start_date, 'end_date': end_date})
    monthly_rider_information = cursor.fetchall()

    connection.commit()
    cursor.close()
    connection.close()

    return monthly_rider_information

def main():

    st.write("# Riders Details")

    st.write("### Aggregate Analytics")

    results = orders_by_riders_status()
    data = {'rider_name': [], 'status': [], 'count': []}
    for rider_name, status, count in results:
        data['rider_name'].append(rider_name)
        data['status'].append(status)
        data['count'].append(count)
    fig = px.bar(data, x='rider_name', y='count', color='status', barmode='group')
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.write("### Individual Analytics by Rider")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_date = st.date_input("Select start date", value=pd.Timestamp.today().replace(day=1))
    with col2:
        end_date = st.date_input("Select end date", value=pd.Timestamp.today())

    with col4:
        selected_rider_name = st.selectbox("Select rider", [rider[1] for rider in riders_list()])
    selected_rider_id = next((rider[0] for rider in riders_list() if rider[1] == selected_rider_name), None)
    data = monthly_rider_information(selected_rider_id, start_date, end_date)

    df = pd.DataFrame(data, columns=['day', 'completed_order_count', 'denied_order_count'])
    fig = px.line(df, x='day', y=['completed_order_count', 'denied_order_count'],
                  labels={'day': 'Date', 'value': 'Count'},
                  title='Completed vs Refused Orders for Selected Rider')

    # Customizing line colors
    fig.update_traces(line=dict(color='blue'), selector=dict(name='completed_order_count'))
    fig.update_traces(line=dict(color='red'), selector=dict(name='denied_order_count'))

    # Customizing legend labels
    fig.update_layout(
        legend_title_text=None,  # No legend title
        legend=dict(
            traceorder='normal',  # Keep the legend items in the order they are specified
            font=dict(size=10),  # Font size of the legend items
            itemsizing='constant',  # Maintain constant legend item sizes
            tracegroupgap=0  # Set the gap between legend items to 0
        )
    )

    # Add custom legend labels
    fig.for_each_trace(
        lambda t: t.update(name='# completed orders' if t.name == 'completed_order_count' else '# refused orders'))

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()