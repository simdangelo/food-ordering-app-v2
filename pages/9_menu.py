# import streamlit as st  # web development
# import numpy as np  # np mean, np random
# import pandas as pd  # read csv, df manipulation
# import time  # to simulate a real time data, time loop
# import plotly.express as px  # interactive charts
# import psycopg2
# import plotly.figure_factory as ff
# from common.postgres_connection import create_postgres_connection
#
#
# st.set_page_config(
#     page_title='Real-Time Food-Order Dashboard',
#     page_icon='✅',
#     layout='wide'
# )
#
# connection, cursor = create_postgres_connection()
#
# placeholder = st.empty()
#
# with placeholder.container():
#     st.write("## Entire menu")
#     cursor.execute("""
#                     SELECT *
#                     FROM food_ordering.Menu_Items
#                 """)
#     results = cursor.fetchall()
#
#     columns = [desc[0] for desc in cursor.description]
#     pandas_results = pd.DataFrame(results, columns=columns)
#     st.dataframe(pandas_results, use_container_width=True, hide_index=True)
#
#     fig_col1, fig_col2 = st.columns(2)
#     with fig_col1:
#         st.write("## Distribution by category")
#         cursor.execute("""
#             SELECT category, COUNT(*) AS category_cardinality
#             FROM food_ordering.Menu_Items
#             GROUP BY category;
#         """)
#         results = cursor.fetchall()
#
#         # Convert the results to a format suitable for Plotly Express
#         data = {'category': [], 'category_cardinality': []}
#         for category, category_cardinality in results:
#             data['category'].append(category)
#             data['category_cardinality'].append(category_cardinality)
#
#         fig1 = px.pie(data, names='category', values='category_cardinality')
#         fig1.update_traces(textinfo='percent+label', textfont_size=14, hole=.3, textposition='auto', showlegend=False)  # Add labels with percentages
#         fig1.update_layout(showlegend=False)  # Remove the legend
#         st.write(fig1)
#
#     with fig_col2:
#         st.write("## Distribution by price")
#         cursor.execute("""
#             SELECT price, COUNT(*) AS price_cardinality
#             FROM food_ordering.Menu_Items
#             GROUP BY price;
#         """)
#         results = cursor.fetchall()
#
#         # Convert the results to a format suitable for Plotly Express
#         data = {'price': [], 'price_cardinality': []}
#         for price, price_cardinality in results:
#             data['price'].append(float(price))
#             data['price_cardinality'].append(price_cardinality)
#
#         fig2 = ff.create_distplot([np.array(data['price'])], group_labels=['Price'], show_hist=False) # bin_size=.5
#         fig2.update_layout(xaxis_tickformat='$')
#         st.write(fig2)
import time

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from common.postgres_connection import create_postgres_connection

st.set_page_config(
    page_title='Menu details',
    page_icon='✅',
    layout='wide'
)

# @st.cache_data(ttl=300) # vedi a cosa serve
def fetch_menu_items():
    connection, cursor = create_postgres_connection()

    cursor.execute("SELECT * FROM food_ordering.Menu_Items")
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    pandas_results = pd.DataFrame(results, columns=columns)

    cursor.close()
    connection.close()
    return pandas_results


placeholder = st.empty()

with placeholder.container():
    menu_items = fetch_menu_items()
    st.write("## Entire menu")
    st.dataframe(menu_items, use_container_width=True, hide_index=True)

    fig_col1, fig_col2 = st.columns(2)
    with fig_col1:
        st.write("## Distribution by category")
        category_counts = menu_items['category'].value_counts()
        fig1 = px.pie(names=category_counts.index, values=category_counts.values)
        fig1.update_traces(textinfo='percent+label', textfont_size=14, hole=.3, textposition='auto', showlegend=False)
        st.write(fig1)

    with fig_col2:
        st.write("## Distribution by price")
        menu_items['price'] = menu_items['price'].astype(float)
        fig2 = ff.create_distplot([np.array(menu_items['price'])], group_labels=['Price'], show_hist=False)
        fig2.update_layout(xaxis_tickformat='$')
        st.write(fig2)
