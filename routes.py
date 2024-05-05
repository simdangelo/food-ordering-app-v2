from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import psycopg2
import json
from kafka import KafkaProducer
from common.kafka_topic import ORDERS_KAFKA_TOPIC
from common.postgres_connection import create_postgres_connection


app = Flask(__name__)

# Kafka producer to send order messages
# producer = KafkaProducer(bootstrap_servers=['localhost:9092'], value_serializer=lambda x: json.dumps(x).encode('utf-8'))
producer = KafkaProducer(bootstrap_servers="localhost:29092")

app.secret_key = 'your_secret_key'

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'rider_id' in session:
        return redirect(url_for('view_orders'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn, cur = create_postgres_connection()
        cur.execute("SELECT rider_id, name FROM food_ordering.riders WHERE name = %s AND password = %s", (username, password))
        rider_info = cur.fetchone()  # Fetch both rider_id and rider_name
        cur.close()
        conn.close()
        if rider_info:
            session['rider_id'] = rider_info[0]
            session['rider_name'] = rider_info[1]  # Store rider_name in session
            return redirect(url_for('view_orders'))
        else:
            return render_template('login.html', error='Invalid username or password.')
    return render_template('login.html', error=None)

@app.route('/view_orders')
def view_orders():
    if 'rider_id' in session:
        rider_id = session['rider_id']
        rider_name = session['rider_name']
        conn, cur = create_postgres_connection()
        cur.execute("""
            SELECT
                a.order_id,
                a.rider_id,
                a.status,
                b.event_timestamp AS order_creation_timestamp,
                CASE
                    WHEN a.status = 'accepted' THEN a.event_timestamp
                    ELSE (
                        SELECT 
                            a_accepted.event_timestamp
                        FROM 
                            food_ordering.orders_status a_accepted
                        WHERE 
                            a_accepted.order_id = a.order_id
                            AND a_accepted.status = 'accepted'
                    )
                END AS order_acceptance_timestamp,
                CASE
                    WHEN a.status = 'completed' THEN a.event_timestamp
                    ELSE NULL
                END AS order_completion_timestamp,
                c.total_amount
            FROM 
                food_ordering.orders_status a
            LEFT JOIN 
                food_ordering.orders_status b ON a.order_id = b.order_id
            LEFT JOIN 
                food_ordering.orders c ON a.order_id = c.order_id
            WHERE 
                a.rider_id = %s
                AND (a.status = 'accepted' OR a.status = 'completed')
                AND b.status = 'pending'
                AND (
                    a.status = 'completed' OR
                    (
                        a.status = 'accepted' AND
                        NOT EXISTS (
                            SELECT 1 FROM food_ordering.orders_status 
                            WHERE order_id = a.order_id AND status = 'completed'
                        )
                    )
                )
            ORDER BY 
                order_acceptance_timestamp DESC;
        """, (rider_id,))

        columns = [desc[0] for desc in cur.description]
        assigned_orders = [dict(zip(columns, row)) for row in cur.fetchall()]

        cur.close()
        conn.close()
        return render_template('view_orders.html', assigned_orders=assigned_orders, rider_id=rider_id, rider_name=rider_name)
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('rider_id', None)
    return redirect(url_for('login'))

def get_menu_items():
    conn, cur = create_postgres_connection()
    cur.execute("SELECT item_id, name, category FROM food_ordering.Menu_Items")
    menu_items = cur.fetchall()
    cur.close()
    conn.close()
    return menu_items

def ingest_order(order):
    conn, cur = create_postgres_connection()

    try:
        cur.execute("""
                        INSERT INTO food_ordering.users (email, phone_number, city)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (email) DO NOTHING;
                    """, (order['email'], order['phone_number'], order['city']))  # Password set to NULL

        total_amount = 0  # Initialize total amount
        order_details = [] # store data details for the current order to store it into Order_Details table

        # order['order_info'] is a dictionary with "item_id" as key and "quantity" as value
        for item_id, quantity in order['order_info'].items():
            cur.execute("SELECT price FROM food_ordering.menu_items WHERE item_id = %s", (item_id,))
            cost = cur.fetchone()[0]
            subtotal = cost * quantity # cost of each specific item
            total_amount = total_amount + (cost * quantity) # cost of the entire order

            # Append order details of each specific item of this order -> 2 item in the order means 2 elements in this list
            order_details.append((item_id, quantity, subtotal))

        # Inserting data into ORDERS table (1 row per order)
        cur.execute("""
                    INSERT INTO food_ordering.orders (user_id, order_created_timestamp, total_amount, status, delivery_city, delivery_instructions)
                    VALUES ((SELECT user_id FROM food_ordering.users WHERE email = %s), %s, %s, %s, %s, %s)
                    RETURNING order_id;
                    """, (order['email'], order['order_created_timestamp'], total_amount, 'pending', order['city'], order.get('delivery_instructions', None)))

        # fetch the order_id of the order just done
        order_id = cur.fetchone()[0]

        # update orders_status to keep track the status changes
        cur.execute("""
                    INSERT INTO food_ordering.orders_status (order_id, status, rider_id, event_timestamp)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (order_id, 'pending', None, order['order_created_timestamp']))

        # inserting data into ORDER_DETAILS about each item in this order
        cur.executemany("""
                    INSERT INTO food_ordering.order_details (order_id, item_id, quantity, subtotal)
                    VALUES (%s, %s, %s, %s);
                    """, [(order_id, item_id, quantity, subtotal) for item_id, quantity, subtotal in order_details])

        conn.commit()
        return order_id
    except psycopg2.Error as e:
        conn.rollback()
        print("Error inserting data:", e)
        return False
    finally:
        cur.close()
        conn.close()


# Modified make_order function
@app.route("/make_order", methods=["GET", "POST"])
def make_order():
    if request.method == "POST":
        email = request.form.get("email")
        phone_number = request.form.get("phone_number")
        order_info = json.loads(request.form.get("orderData"))
        city = request.form.get("city")
        delivery_instructions = request.form.get("delivery_instructions")

        if email and phone_number and order_info and city:
            order = {
                "email": email,
                "phone_number": phone_number,
                "order_info": order_info,
                "city": city,
                "order_created_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "delivery_instructions": delivery_instructions,
            }

            # Ingest order data into tables
            order_id = ingest_order(order)
            if order_id:
                order["order_id"] = order_id
                producer.send(
                    ORDERS_KAFKA_TOPIC,
                    json.dumps(order).encode("utf-8")
                )
                return redirect(url_for('order_confirmation'))  # Redirect to order confirmation page
            else:
                return "Error processing order. Please try again later."
        else:
            return "Invalid order details!"


    menu_items = get_menu_items()

    return render_template("make_order.html", menu_items=menu_items)


@app.route("/order_confirmation")
def order_confirmation():
    return render_template("order_confirmation.html")

@app.route("/orders_db")
def display_orders():
    conn, cursor = create_postgres_connection()
    cursor.execute("SELECT * FROM spark_streams.orders ORDER BY time DESC LIMIT 20;")

    columns = [desc[0] for desc in cursor.description]
    orders = [dict(zip(columns, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template('orders_display.html', orders=orders)


@app.route('/update_order', methods=['POST'])
def update_order():
    order_id = str(request.form['orderId'])
    rider_id = str(request.form['riderId'])

    conn, cursor = create_postgres_connection()
    cursor.execute("""
                    INSERT INTO food_ordering.orders_status (order_id, status, rider_id, event_timestamp)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, "completed", rider_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    cursor.close()
    conn.commit()
    conn.close()

    return jsonify(status='success')


if __name__ == "__main__":
    app.run(debug=True)