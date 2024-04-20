import logging

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from common.kafka_topic import *
import psycopg2


def create_spark_connection():
    s_conn = None

    try:
        s_conn = (
            SparkSession.builder
            .appName('SparkDataStreaming')
            .config('spark.jars.packages', "com.datastax.spark:spark-cassandra-connector_2.12:3.5.0,"
                                           "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                                           "org.postgresql:postgresql:42.6.0",)
            .config('spark.cassandra.connection.host', 'localhost:9042')
            .getOrCreate()
        )

        # s_conn.sparkContext.setLogLevel("ERROR")
        logging.info("Spark connection created successfully!")
    except Exception as e:
        logging.error(f"Couldn't create the spark session due to exception {e}")

    return s_conn


def connect_to_kafka(spark_conn):
    spark_df = None
    try:
        spark_df = (
            spark_conn.readStream
            .format('kafka')
            .option('kafka.bootstrap.servers', 'localhost:29092')
            .option('subscribe', ORDER_CONFIRMED_KAFKA_TOPIC)
            .option('startingOffsets', 'earliest')
            # .option("failOnDataLoss", "false") # in case of specific error, you need to set this option
            .load()
        )
        logging.info("kafka dataframe created successfully")
    except Exception as e:
        logging.warning(f"kafka dataframe could not be created because: {e}")

    return spark_df

def create_selection_df_from_kafka(spark_df):
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("username", StringType(), False),
        StructField("email", StringType(), False),
        StructField("food", StringType(), False),
        StructField("size", StringType(), False),
        StructField("cost", IntegerType(), False),
        StructField("time", TimestampType(), False),
        StructField("order_completed", IntegerType(), False),
    ])

    sel = spark_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col('value'), schema).alias('data')).select("data.*")
    print(sel)

    return sel

def test_postgres_connection(host, database, user, password, port):
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        conn.close()
        print("Connection to PostgreSQL successful!")

    except psycopg2.Error as e:
        # Print error message if connection fails
        print(f"Error connecting to PostgreSQL: {e}")

def create_postgres_connection():
    conn = psycopg2.connect(
        host='localhost',
        database='database',
        user='user',
        password='password',
        port=5432
    )

    return conn

def create_postgres_schema(postgres_connection):
    cursor = postgres_connection.cursor()
    cursor.execute(
        """
        CREATE SCHEMA IF NOT EXISTS spark_streams;
        """
    )
    cursor.close()
    postgres_connection.commit()

def create_postgres_table(postgres_connection):
    cursor = postgres_connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spark_streams.orders (
            id VARCHAR(255) PRIMARY KEY,
            username VARCHAR(255),
            email VARCHAR(255),
            food VARCHAR(255),
            size VARCHAR(255),
            cost DECIMAL,
            time TIMESTAMP,
            order_completed INT
            );
        """)
    cursor.close()
    postgres_connection.commit()

    print("Table created successfully!")



if __name__ == "__main__":
    # define postgres parameters
    host = 'localhost'
    database = 'database'
    user = 'user'
    password = 'password'
    port = 5432

    # create spark connection
    spark_conn = create_spark_connection()

    spark_df = connect_to_kafka(spark_conn)
    selection_df = create_selection_df_from_kafka(spark_df)

    test_postgres_connection(host, database, user, password, port)
    postgres_connection = create_postgres_connection()
    create_postgres_schema(postgres_connection)
    create_postgres_table(postgres_connection)

    logging.info("Streaming is being started...")


    def write_stream_to_postgres(batch_df, epoch_id):
        batch_df.write \
            .mode("append") \
            .format("jdbc") \
            .option("url", f"jdbc:postgresql://localhost:5432/database") \
            .option("driver", "org.postgresql.Driver") \
            .option("user", user) \
            .option("password", password) \
            .option("dbtable", "spark_streams.orders") \
            .save()

    # Start streaming query
    streaming_query = selection_df.writeStream \
        .foreachBatch(write_stream_to_postgres) \
        .start()

    # DEBUG IN CONSOLE
    # selection_df.printSchema()
    # streaming_query = selection_df \
    #     .writeStream \
    #     .outputMode("append") \
    #     .format("console") \
    #     .start()

    # Await termination
    streaming_query.awaitTermination()