from selenium import webdriver
import time
import pandas as pd
import numpy as np
import folium
import os
from googletrans import Translator
import json
import datetime
import sqlite3

#Country class for future planned API feed
class Country:
    name = ""
    total_cases = ""
    new_cases = ""
    total_deaths = ""
    new_deaths = ""
    total_recovered = ""
    active_cases = ""
    critical_cases = ""
    tot_cases_per_1m = ""
    tot_deaths_per_1m = ""
    first_case = ""

    def __init__(self, name, total_cases, new_cases, total_deaths, new_deaths, total_recovered, active_cases, critical_cases, tot_cases_per_1m, tot_deaths_per_1m, first_case):
        self.name = name
        self.total_cases = total_cases
        self.new_cases = new_cases
        self.total_deaths = total_deaths
        self.new_deaths = new_deaths
        self.total_recovered = total_recovered
        self.active_cases = active_cases
        self.critical_cases = critical_cases
        self.tot_cases_per_1m = tot_cases_per_1m
        self.tot_deaths_per_1m = tot_deaths_per_1m
        # self.first_case = first_case


    def __init__(self,lst):
        self.name = lst[0]
        self.total_cases = lst[1]
        self.new_cases = lst[2]
        self.total_deaths = lst[3]
        self.new_deaths = lst[4]
        self.total_recovered = lst[5]
        self.active_cases = lst[6]
        self.critical_cases = lst[7]
        self.tot_cases_per_1m = lst[8]
        self.tot_deaths_per_1m = lst[9]
        # self.first_case = lst[10]

    def __str__(self):
        return "Country Name: " + self.name + ", Total Cases: " + self.total_cases


# Selenium configurations
driver_path = "\\driver\\chromedriver"
full_path = os.getcwd() + driver_path
print(full_path)

options = webdriver.ChromeOptions()
options.add_argument('headless')

browser = webdriver.Chrome(executable_path=full_path, options=options)
url = "https://www.worldometers.info/coronavirus/"

# Location, name and extension of the map to be created
map_path = "mymap.html"

# Translator object to translate country names
translator = Translator(service_urls=["translate.google.com.tr"])

# NumPy array to hold data and convert to Pandas DataFrame
# data_old = np.array([["", "TotalCases", "NewCases", "TotalDeaths", "NewDeaths", "TotalRecovered", "ActiveCases", "CriticalCases", "TotCasesPer1M", "TotDeathsPer1M", "FirstCase"],
#                  ])
data = np.array([["", "TotalCases", "NewCases", "TotalDeaths", "NewDeaths", "TotalRecovered", "ActiveCases", "CriticalCases", "TotCasesPer1M", "TotDeathsPer1M"],
                 ])

# Countries array to hold each country as an object
countries = []

# Update time of data
update_time = ""

# Database configs
db = sqlite3.connect("db.sqlite")


def main():
    #create_database()

    get_countries()

    insert_countrydata_to_database()

    create_map()

    db.close()


def get_countries():
    global data, countries, browser, update_time
    browser.get(url=url)
    time.sleep(2)
    country_rows = browser.find_elements_by_xpath("//div[@id='nav-today']//tbody[1]//tr")
    # print(country_rows)
    num_of_countries = len(country_rows)

    columns = browser.find_elements_by_xpath("//div[@id='nav-today']//tbody[1]//tr[1]//td")
    # print(columns)
    num_of_cols = len(columns)

    print("num_of_countries: ", num_of_countries)
    # print(num_of_cols)

    update_time = datetime.datetime.now().strftime("%d.%m.%Y, %H:%M:%S")

    for i in range(num_of_countries):
        raw_data = []
        for j in range(10):
            appended_text = browser.find_element_by_xpath("//tbody[1]//tr["+ str(i+1) +"]//td[" + str(j+1) + "]").text.replace(',', '')
            if appended_text == "":
                appended_text = "0"
            if any(char.isdigit() for char in appended_text) and j != 10:
                raw_data.append(float(appended_text))
            else:
                raw_data.append(appended_text)
        print("rawdata:", raw_data)
        new_country = Country(raw_data)
        countries.append(new_country)

        raw_data = [raw_data]
        raw_data = np.array(raw_data)

        data = np.concatenate((data, raw_data))

    data = pd.DataFrame(data=data[1:, 1:],
                       index=data[1:, 0],
                       columns=data[0, 1:])


    # types_old = {"TotalCases": float, "NewCases": float, "TotalDeaths": float,"NewDeaths": float,
    #          "TotalRecovered": float, "ActiveCases": float, "CriticalCases": float, "TotCasesPer1M": float,
    #          "TotDeathsPer1M": float, "FirstCase": str,
    #          }
    types = {"TotalCases": float, "NewCases": float, "TotalDeaths": float, "NewDeaths": float,
             "TotalRecovered": float, "ActiveCases": float, "CriticalCases": float, "TotCasesPer1M": float,
             "TotDeathsPer1M": float,
             }
    data = data.astype(types)
    print(data)
    browser.quit()


def create_map():

    global translator, update_time

    # Number of Total Cases in all around the world
    total_cases = data[1:].TotalCases.sum()
    total_deaths = data[1:].TotalDeaths.sum()

    # Empty Folium Map with that uses Open Street Map as a tile
    m = folium.Map(location=[39.933333333333,32.866667], tiles='OpenStreetMap', zoom_start=5)

    # Title of map
    title = "<div class='container'><h1 class='text-center'>CoronaVirus (Covid-19) Haritası</h1><center>Güncelleme Zamanı: {t1}</center></div>".format(t1=update_time)
    m.get_root().html.add_child(folium.Element(title))

    # CSV file for marking each country on its capitals. This file contains countries information which are name and coordinates of capitals and region of country
    capitals = pd.read_csv('countries.csv')

    print("Number of countries", data.shape[0])

    # Minimum radius for marking countries with circle
    min_radius = 50000

    # For every country in countries array on global, loop draw circle with respect to number of total cases in country
    for country in countries[1:]:
        temp = capitals[capitals.CountryName == country.name]
        print("CountryName: ", country.name)
        temp = temp.reset_index()
        print(temp.iloc[0].CapitalName)

        #print("Total Cases: ", total_cases)
        print("Case:", country.total_cases)
        radius = (int(country.total_cases)/int(total_cases))*2000000
        radius += min_radius
        print("Radius:", radius)

        country_name = ""

        try:
            country_name = translator.translate(temp.iloc[0].ActualName, src="en", dest="tr").text
        except json.decoder.JSONDecodeError:
            print("googletrans json error")
        finally:
            country_name = temp.iloc[0].ActualName

        text = "<div><h4>" + country_name + "</h4><h5>Vaka Sayısı: " + str(int(country.total_cases)) + "</h5><h5>Ölü Sayısı: " + str(int(country.total_deaths)) + "</h5></div>"
        popup = folium.Popup(html=text, max_width=200, min_width=150, sticky=False)
        tooltip = folium.Tooltip(text=country_name)
        folium.Circle(
            location=(temp.iloc[0].CapitalLatitude, temp.iloc[0].CapitalLongitude),
            popup=popup,
            radius=(radius if radius > min_radius else min_radius),
            color='red',
            fill=True,
            fill_color='red',
            tooltip=tooltip
        ).add_to(m)

    item_txt = """<br> &nbsp; Vaka Sayısı: &nbsp; {total_cases} <br> &nbsp; Ölü Sayısı:  &nbsp; {total_deaths}"""
    html_itms = item_txt.format(total_cases=int(total_cases), total_deaths=int(total_deaths))

    legend_html = """
         <div style="
         position: fixed; 
         bottom: 50px; left: 50px; width: 200px; height: 160px; 
         border:2px solid black; z-index:9999; 

         font-size:14px;
         font-weight: bold;
         background: white;

         ">
         <center><h4>{title}</h4></center>
         <hr>

         {itm_txt}

          </div> """.format(title="Dünya Geneli", itm_txt=html_itms)
    m.get_root().html.add_child(folium.Element(legend_html))

    # folium.GeoJson(data="countries.geo.json", name="geojson").add_to(m)

    m.save(map_path)

    print("You can find map file at: ", os.path.join(os.getcwd(), map_path))

    html_head = m.get_root().header.render()
    html_body = m.get_root().html.render()
    html_script = m.get_root().script.render()

    # print("head: ", html_head)
    # print("body: ", html_body)
    # print("script: ", html_script)


def create_database():
    global db
    cursor = db.cursor()
    continent_query = 'CREATE TABLE "continent" ("continent_id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, ' \
                      '"continent_name"	TEXT NOT NULL UNIQUE, "continent_code"	TEXT NOT NULL UNIQUE)'
    cursor.execute(continent_query)

    country_query = 'CREATE TABLE "country" ("country_id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,' \
                    '"country_name"	TEXT NOT NULL UNIQUE, "country_capital_name" TEXT NOT NULL, ' \
                    '"country_capital_latitude"	INTEGER NOT NULL, "country_capital_longitude" INTEGER NOT NULL,' \
                    '"country_code"	TEXT, "country_continent" INTEGER NOT NULL,"country_actual_name" INTEGER NOT NULL,'\
                    'FOREIGN KEY("country_continent") REFERENCES "continent"("continent_id"))'
    cursor.execute(country_query)

    data_query = 'CREATE TABLE "data" ("data_id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, ' \
                 '"data_country" INTEGER NOT NULL UNIQUE, "data_total_cases" INTEGER, "data_new_cases" INTEGER, ' \
                 '"data_total_deaths" INTEGER, "data_total_recovered" INTEGER, "data_active_cases" INTEGER, ' \
                 '"data_critical_cases" INTEGER, "data_tot_cases_per_1m" REAL, "data_tot_deaths_per_1m"	REAL, ' \
                 '"data_first_case"	TEXT, FOREIGN KEY("data_country") REFERENCES "country"("country_id"))'
    cursor.execute(data_query)

    db.commit()

    add_continents_to_database()
    add_countries_to_database()

    print("Database Created.")


def add_continents_to_database():
    global db
    cursor = db.cursor()
    continents_csv = pd.read_csv('continents.csv')

    for index, row in continents_csv.iterrows():
        query = 'insert into continent("continent_name", "continent_code") values("{v1}", "{v2}")'
        query = query.format(v1=row['ContinentName'], v2=row['ContinentCode'])
        print(query)
        cursor.execute(query)

    db.commit()


def add_countries_to_database():
    global db
    cursor = db.cursor()
    countries_csv = pd.read_csv('countries.csv')

    for index, row in countries_csv.iterrows():
        query = 'insert into country("country_name", "country_capital_name", "country_capital_latitude", ' \
                '"country_capital_longitude", "country_code", "country_continent", "country_actual_name") ' \
                'values("{v1}", "{v2}", {v3}, {v4}, "{v5}", ' \
                '(select continent_id from continent where continent_name="{v6}"), "{v7}")'
        query = query.format(v1=row['CountryName'], v2=row['CapitalName'], v3=row['CapitalLatitude'],
                             v4=row['CapitalLongitude'], v5=row['CountryCode'], v6=row['ContinentName'],
                             v7=row['ActualName'])
        print(query)
        cursor.execute(query)

    db.commit()

def insert_countrydata_to_database():
    global countries, db
    cursor = db.cursor()

    for country in countries[1:]:
        check_query = 'select data_id from data where data_country = ' \
                      '(select country_id from country where country_name = "{v1}")'.format(v1=country.name)
        cursor.execute(check_query)
        check = cursor.fetchall()
        print(check)
        if check == []:
            print("{country} is not in the table named data. It will be added automatically.".format(country=country.name))
            add_country_to_data_query = 'insert into data("data_country", "data_total_cases", "data_new_cases", ' \
                                        '"data_total_deaths", "data_new_deaths", "data_total_recovered", ' \
                                        '"data_active_cases", "data_critical_cases", "data_tot_cases_per_1m", ' \
                                        '"data_tot_deaths_per_1m") ' \
                                        'values((select country_id from country where country_name = "{v1}"), {v2}, {v3}, {v4}, {v5}, {v6}, {v7}, {v8}, {v9}, {v10})'
            add_country_to_data_query = add_country_to_data_query.format(v1=country.name, v2=country.total_cases, v3=country.new_cases, v4=country.total_deaths,
                                                                         v5=country.new_deaths, v6=country.total_recovered, v7=country.active_cases,
                                                                         v8=country.critical_cases, v9=country.tot_cases_per_1m, v10=country.tot_deaths_per_1m)
            print(add_country_to_data_query)
            cursor.execute(add_country_to_data_query)
            db.commit()
        else:
            print("{country} is in the table named data. It's data will be updated.".format(country=country.name))
            update_country_query = 'update data set data_total_cases = {v2}, data_new_cases = {v3}, ' \
                                   'data_total_deaths = {v4}, data_new_deaths = {v5}, data_total_recovered={v6}, ' \
                                   'data_active_cases={v7}, data_critical_cases={v8}, data_tot_cases_per_1m={v9}, '\
                                   'data_tot_deaths_per_1m = {v10} '\
                                   'where data_country = (select country_id from country where country_name = "{v1}")'
            update_country_query = update_country_query.format(v1=country.name, v2=country.total_cases, v3=country.new_cases, v4=country.total_deaths,
                                                               v5=country.new_deaths, v6=country.total_recovered, v7=country.active_cases,
                                                               v8=country.critical_cases, v9=country.tot_cases_per_1m, v10=country.tot_deaths_per_1m)
            print(update_country_query)
            cursor.execute(update_country_query)
            db.commit()


if __name__ == "__main__":
    main()