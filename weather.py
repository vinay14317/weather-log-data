import os
import requests
import re
import mysql.connector
import logging
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    filename="weather_app.log",
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(funcName)s | %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S"
)


#====Database conection====
def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("Hostname"),
            user=os.getenv("db_userName"),
            password=os.getenv("Password"),
            database=os.getenv("Databasename")
        )
        #print("Connection successful")
        #logging.info("Database Connected Successfully")
        return conn 
        

    except Exception as e:
        logging.error("DATABASE CONNECTION FAILED")
        print("MySQL Error:", e)
        return None

#======creating table======
def create_table():
    conn = None
    cursor = None

    try:
        conn = get_connection()

        if conn is None:
            print("Database connection failed")
            return

        cursor = conn.cursor()

        query = """
        CREATE TABLE IF NOT EXISTS weather_data(
            id INT PRIMARY KEY AUTO_INCREMENT,
            city VARCHAR(30),
            country VARCHAR(30),
            temperature FLOAT,
            humidity INT,
            wind_speed FLOAT,
            weather_condition VARCHAR(100),
            search_date DATE,
            search_time TIME
        )
        """

        cursor.execute(query)
        conn.commit()
        print("Table created successfully!")

    except Exception as e:
        print("Error:", e)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()
            
            
            
def get_weather_info(city):
    logging.info(f"Fetching weather for {city}")

    url="http://api.weatherapi.com/v1/current.json"

    query_params={
        "key":os.getenv("API_Key"),
        "q":city
    }

    try:
        
        request=requests.get(url,params=query_params)

        if request.status_code == 200:
            logging.info(f"Weather data received for {city}")
            return request.json()
        else:
            logging.critical("SERVER DOWN")
            logging.error(f"API Error {request.status_code} for city {city}"
            )
            return None
    except Exception as e:
         logging.error(f"Weather API Error: {e}")
         return None

# ========================= # VALIDATION FUNCTIONS # ========================= 
def validate_city(City): 
    return bool(re.fullmatch(r"[A-Za-z]+(?:[ .][A-Za-z]+)*", City)) 
def validate_country(Country): 
    return bool(re.fullmatch(r"[A-Za-z]+(?: [A-Za-z]+)*", Country)) 
def validate_temperature(Temperature): 
    return bool(re.fullmatch(r"-?\d+(\.\d+)?", str(Temperature))) 
def validate_humidity(Humidity): 
    return bool(re.fullmatch(r"\d+", str(Humidity))) 
def validate_wind_speed(Wind_Speed): 
    return bool(re.fullmatch(r"\d+(\.\d+)?", str(Wind_Speed)))
def validate_condition(weather_condition): 
    return bool(re.fullmatch(r"[A-Za-z]+(?: [A-Za-z]+)*", weather_condition))

# ========================= # VALIDATION REPORT # ========================= 
def validate_weather_data(city, Country, Temperature, Humidity, Wind_Speed, weather_condition): 
    city_status = validate_city(city) 
    country_status = validate_country(Country) 
    temp_status = validate_temperature(Temperature) 
    humidity_status = validate_humidity(Humidity) 
    wind_status = validate_wind_speed(Wind_Speed) 
    condition_status = validate_condition(weather_condition) 
    
    print("\nVALIDATION REPORT"),print("-" * 40) 
    print("CITY VALIDATION :", "PASSED" if city_status else "FAILED") 
    print("COUNTRY VALIDATION :", "PASSED" if country_status else "FAILED") 
    print("TEMPERATURE VALIDATION :", "PASSED" if temp_status else "FAILED") 
    print("HUMIDITY VALIDATION :", "PASSED" if humidity_status else "FAILED") 
    print("WIND SPEED VALIDATION :", "PASSED" if wind_status else "FAILED") 
    print("CONDITION VALIDATION :", "PASSED" if condition_status else "FAILED") 
    return all([ city_status, country_status, temp_status, humidity_status, wind_status, condition_status ])

    
#======Save to Mysql====== 
def save_mysql(weather):

    try:
        City = weather["location"]["name"]
        Country = weather["location"]["country"]
        Temperature = weather["current"]["temp_c"]
        Humidity = weather["current"]["humidity"]
        Wind_Speed = weather["current"]["wind_kph"]
        weather_condition = weather["current"]["condition"]["text"]

        if not validate_weather_data(
            City,
            Country,
            Temperature,
            Humidity,
            Wind_Speed,
            weather_condition
        ):
            print("Validation failed. Data not saved.")
            logging.warning("Vaildation is Unsccessful")
            return

        conn = get_connection()

        if not conn:
            return

        cursor = conn.cursor()

        now = datetime.now()

        query = """
        INSERT INTO weather_data(
        city,country,temperature,humidity,
        wind_speed,weather_condition,
        search_date,search_time)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            City,
            Country,
            Temperature,
            Humidity,
            Wind_Speed,
            weather_condition,
            now.date(),
            now.time()
        )

        cursor.execute(query, values)
        conn.commit()
        logging.info(f"Weather saved: {City} | {Temperature}°C | {weather_condition}")

        print("Weather data saved successfully.")

    except Exception as e:
        logging.error("Weather data not saved...")
        print("Error:", e)

    finally:
            cursor.close()
            conn.close()
            

#======Display data=====
def display_data(weather):
    print("-" * 30)
    print("Weather Report")
    print("-" * 30)
    print("City:", weather["location"]["name"])
    print("Country:", weather["location"]["country"])
    print("Temperature:", weather["current"]["temp_c"], "°C")
    print("Humidity:", weather["current"]["humidity"], "%")
    print("Wind Speed:", weather["current"]["wind_kph"], "km/h")
    print("Condition:", weather["current"]["condition"]["text"])

def check_weather():
    city=input("Enter city name: ")

    # Validate city name
    if re.fullmatch(r"[A-Za-z\s]+", city):
        print("Valid city name\n")
        logging.info("vaild city name....")
    else:
        print("Invalid city name\n")
        logging.warning("Enter vaild city name")
        return
    
    weather=get_weather_info(city)
    if weather:
        
        display_data(weather)
        save_mysql(weather)
    else:
        print("Unable to fetch weather data.")

#===View Weather History===
def view_history():
    try:
        conn=get_connection()
        cursor=conn.cursor()

        query="""
        select id,city,temperature,weather_condition,search_date,search_time from weather_data """
         
        cursor.execute(query)
        record=cursor.fetchall()
        print("\n========== WEATHER HISTORY ==========")
        for rec in record:
             print(
                f" ID: {rec[0]}, |"
                f" City: {rec[1]}, |"
                f" Temp: {rec[2]}°C, |"
                f" weather_condition: {rec[3]}, | "
                f" Date: {rec[4]}, |"
                f" Time: {rec[5]}"
    )
        print("\nRecord fetch Successfully...")
        logging.info("Weather History Viewed")  
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

#=====Display Last Weather Search=====
def last_search():
    try:
        conn=get_connection()
        cursor=conn.cursor()
        query="""select *from weather_data order by id desc limit 1 """
        cursor.execute(query)
        record=cursor.fetchone()

        if record:
            print("\n==Last Weather Search==== ")
            print(f" ID: {record[0]}, |"
                  f" City: {record[1]}, |"
                  f" Country: {record[2]}, |"
                  f" Temperature: {record[3]}°C,|"
                  f" Humidity: {record[4]},|"
                  f" Wind Speed: {record[5]},|"
                  f" weather_condition: {record[6]}, |"
                  f" Date: {record[7]}, |"
                  f" Time: {record[8]} ")
            
        logging.info("Last Weather Search Viewed")
            
            
    except Exception as e:
        print("Weather record not found..",e)
    finally:
        cursor.close()
        conn.close()

#=====Display Hottest City===
def hottest_city():
    try:
        conn=get_connection()
        cursor=conn.cursor()
        query="""select city,temperature,weather_condition from weather_data order by temperature desc limit 1 """
        cursor.execute(query)
        hot=cursor.fetchone()
        if hot :
            print("\n== Hottest City ==== ")
            print(hot)
            logging.info("Hottest City Viewed")
        else:
            print("No record")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

#======Display Coldest City===
def coldest_city():
    try:
        conn=get_connection()
        cursor=conn.cursor()
        query="""select city,temperature,weather_condition from weather_data order by temperature asc limit 1"""
        cursor.execute(query)
        record=cursor.fetchone()
        if record:
            print("\n== Coldest City ==== ")
            print(record)
            logging.info("Coldest City Viewed")
        else:
            print("No record found")

    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

#=====Weather Search Counter====
def search_counter():
    try:
        conn=get_connection()
        cursor=conn.cursor()
        query="""select count(*) from weather_data"""
        cursor.execute(query)
        count=cursor.fetchone()[0]
        if count:
            print("\n---Weather Search Counter--")
            print("\nTotal Searches:",count)
            logging.info(f"Total Search Count Viewed : {count}")
        else:
            print("No record is found")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

#===Delete Weather History==
def delete_history():
    try:
        conn=get_connection()
        cursor=conn.cursor()
        option=input("Enter your option (yes/no): ")
        if option.lower()=="yes":
            query="""Delete from weather_data"""
            cursor.execute(query)
            conn.commit()
            print("\nHistory Deleted Successfully")
            logging.warning("All Weather History Deleted")
        else:
            print("Enter the correct option")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

#====Export Weather History===
def export_history():
    try:
        conn=get_connection()
        cursor=conn.cursor()
        query="""select city,temperature,weather_condition from weather_data """
        cursor.execute(query)
        records=cursor.fetchall()

        with open("Weather_histoy.csv","w") as file:
            file.write("City,  Temperature,   Weather Condition\n") 
            for i in records:
                data=f"{i[0]},  {i[1]},  {i[2]}\n"

                file.write(data)
        print("Weather history exported successfully.")
        logging.info("Weather History Exported to weather_history.txt")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()





#=====Menu====

def main():
    logging.info("Weather Logger Application Started")
    create_table()
    while True:
        print("\n========== WEATHER LOGGER ==========")
        print("1 --> Check Weather")
        print("2 --> View Weather History")
        print("3 --> Last Weather Search")
        print("4 --> Display Hottest City")
        print("5 --> Display Coldest City")
        print("6 --> Weather Search Counter")
        print("7 --> Delete Weather Historyt")
        print("8 --> Export Weather History")
        print("9 --> Exit")
        try:

            choice=int(input("\nenter your choice: "))
            match choice:
                case 1:
                    check_weather()
                case 2:
                    view_history()
                case 3:
                    last_search()
                case 4:
                    hottest_city()
                case 5:
                    coldest_city()
                case 6:
                    search_counter()
                case 7:
                    delete_history()
                case 8:
                    export_history()
                case 9:
                    print("Thank you !!!")
                    logging.info("Application Closed By User")
                    break
                case _:
                    print("Invalid Choice")
        except ValueError:
            print("Please enter a number")

main()









