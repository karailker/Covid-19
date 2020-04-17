from selenium import webdriver
import time
import pandas as pd
import numpy as np
import folium
from folium import plugins
import os
from googletrans import Translator
import json
import datetime
import sqlite3


# Country class for future planned API feed
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

    def __init__(self, lst):
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


class City:
    name = ""
    number = 0
    shape_type = ""
    coordinates = []
    total_cases = 0
    total_deaths = 0

    def __init__(self, name, number, shape_type, coordinates):
        self.name = name
        self.number = number
        self.shape_type = shape_type
        self.coordinates = coordinates

    def __str__(self):
        return str(self.name) + str(self.number)

    def __eq__(self, other):
        if self.name == other.name:
            return True

    def __ne__(self, other):
        if self.name != other.name:
            return False


# Selenium configurations
driver_path = "\\driver\\chromedriver"
full_path = os.getcwd() + driver_path
print(full_path)

options = webdriver.ChromeOptions()
options.add_argument('headless')

browser = webdriver.Chrome(executable_path=full_path, options=options)
browser.maximize_window()
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

cities = []

# Update time of data
update_time = ""
city_update_time = "11.04.2020"

# Database configs
db = sqlite3.connect("covid-db.sqlite")


def main():
    #create_database()

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
        country_control = browser.find_element_by_xpath("//tbody[1]//tr[" + str(i + 1) + "]//td[1]") \
            .text.replace(',', '')
        # print("country_control:", country_control)
        if country_control != "":
            for j in range(10):
                appended_text = browser.find_element_by_xpath("//tbody[1]//tr[" + str(i+1) + "]//td[" + str(j+1) + "]")\
                    .text.replace(',', '')
                if appended_text == "" or appended_text == "N/A":
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

    get_northern_cyprus()

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

    insert_countrydata_to_database()


def get_northern_cyprus():
    global browser, data, countries
    url = "https://corona.cbddo.gov.tr/"
    browser.get(url)
    time.sleep(0.5)

    textSearch = browser.find_element_by_xpath("//input[@id='txtSearch']")
    textSearch.send_keys("Kuzey Kıbrıs")

    total_cases = browser.find_element_by_xpath("//td[@class='table-row-style table-cell-confirmed sorting_2']").text
    total_deaths = browser.find_element_by_xpath("//td[contains(@class,'table-row-style table-cell-death')]").text
    total_recovered = browser.find_element_by_xpath("//td[contains(@class,'table-row-style table-cell-recovery')]").text

    raw_data = ["Northern Cyprus", total_cases, 0, total_deaths, 0, total_recovered,
                (int(total_cases) - int(total_deaths) - int(total_recovered)), 0, 0, 0]
    print("rawdata:", raw_data)

    northern_cyprus = Country(raw_data)
    countries.append(northern_cyprus)


    raw_data = [raw_data]
    raw_data = np.array(raw_data)

    data = np.concatenate((data, raw_data))


def get_cities():
    global cities

    with open(file='tr-cities.json', encoding='utf-8') as f:
        data = json.load(f)

    # print(json.dumps(data, indent=4, sort_keys=True))

    cities = []

    for feature in data['features']:
        shape_type = feature['geometry']['type']
        coordinates = feature['geometry']['coordinates']
        name = feature['properties']['name']
        number = feature['properties']['number']
        # print(feature['geometry']['type'])
        # print(feature['geometry']['coordinates'])
        # print(feature['properties']['name'])
        # print(feature['properties']['number'])
        new_city = City(name, number, shape_type, coordinates)
        cities.append(new_city)

    # for city in cities:
    #     print(city)

    get_city_data()


def get_city_data():
    global cities
    # print("\nget_city_data")
    cities_csv = pd.read_csv(filepath_or_buffer='cities_cases.csv',encoding="utf-8")
    for city in cities:
        # print(city)
        temp = cities_csv[cities_csv.CityName == city.name]
        # print("CityName: ", city.name)
        temp = temp.reset_index()
        city.total_cases = temp.iloc[0].TotalCases
        city.total_deaths = temp.iloc[0].TotalDeaths
        # print(city.total_cases, city.total_deaths)


def create_geojson(city, country):
    # print("City: ", city.name)

    geojson_data = {"type": "FeatureCollection"}

    features = {}

    geometry = {}
    geometry['type'] = city.shape_type
    geometry['coordinates'] = city.coordinates

    properties = {}
    properties['name'] = city.name
    properties['number'] = city.number
    properties['total_cases'] = str(city.total_cases)
    properties['country_total_cases'] = str(int(country.total_cases))

    # style = {'fillColor': "red", 'fillOpacity': 0.5, }
    # style['fill'] = "red"
    # style['fill-opacity'] = 0.6


    features['geometry'] = geometry
    features['properties'] = properties
    features['type'] = "Feature"
    # features['style'] = style

    geojson_data['features'] = [features]

    geojson_data = json.dumps(geojson_data, ensure_ascii=False)

    # print(geojson_data)

    return geojson_data


def create_map():

    get_countries()
    get_cities()

    global translator, update_time, cities, db, city_update_time

    # Number of Total Cases in all around the world
    total_cases = data[1:].TotalCases.sum()
    total_deaths = data[1:].TotalDeaths.sum()

    # Empty Folium Map with that uses Open Street Map as a tile
    m = folium.Map(location=[39.933333333333,32.866667], tiles='OpenStreetMap', zoom_start=5)

    # Title of map
    title = "<div class='container'><h1 class='text-center'>CoronaVirus (Covid-19) Haritası</h1><center>Güncelleme Zamanı: {t1}, İl Verileri {t2} Tarihine Aittir</center></div>".format(t1=update_time, t2="03.04.2020")
    # m.get_root().html.add_child(folium.Element(title))

    # CSV file for marking each country on its capitals. This file contains countries information which are name and coordinates of capitals and region of country
    capitals = pd.read_csv('countries.csv')

    print("Number of countries", data.shape[0])

    # Minimum radius for marking countries with circle
    min_radius = 50000

    cursor = db.cursor()
    il_feature_group = folium.FeatureGroup(name='İl Verisi')
    ulke_feature_group = folium.FeatureGroup(name="Ülke Verisi", show=False)

    update_time_query = 'update update_time set all_data="{v1}", cities_data="{v2}" where row = 1'.format(
        v1=update_time, v2=city_update_time
    )
    cursor.execute(update_time_query)
    db.commit()

    api_check = False
    try:
        translator.translate("API Control", src="en", dest="tr").text
    except json.decoder.JSONDecodeError:
        print("googletrans json error")
        api_check = False
    else:
        api_check = True

    # For every country in countries array on global, loop draw circle with respect to number of total cases in country
    for country in countries[1:]:

        temp = capitals[capitals.CountryName == country.name]
        print("CountryName: ", country.name)
        temp = temp.reset_index()
        print(temp.iloc[0].CapitalName)

        # print("Total Cases: ", total_cases)
        print("Case:", country.total_cases)
        radius = (int(country.total_cases) / int(total_cases)) * 2000000
        radius += min_radius
        print("Radius:", radius)

        country_name = temp.iloc[0].ActualName

        if api_check:
            try:
                country_name = translator.translate(temp.iloc[0].ActualName, src="en", dest="tr").text
            except json.decoder.JSONDecodeError:
                print("googletrans json error")

        text = "<div><h4>" + country_name + "</h4><h5>Vaka Sayısı: " + str(
            int(country.total_cases)) + "</h5><h5>Ölü Sayısı: " + str(int(country.total_deaths)) + "</h5></div>"
        popup = folium.Popup(html=text, max_width=200, min_width=150, sticky=False)
        tooltip = folium.Tooltip(text=country_name)
        country_Circle = folium.Circle(
            location=(temp.iloc[0].CapitalLatitude, temp.iloc[0].CapitalLongitude),
            popup=popup,
            radius=(radius if radius > min_radius else min_radius),
            color='red',
            fill=True,
            fill_color='red',
            tooltip=tooltip
        )

        if country.name == "Turkey":
            for city in cities:

                # folium.Polygon(city.coordinates).add_to(m)
                city_geojson = create_geojson(city, country)
                percentage = (city.total_cases/country.total_cases)*100
                print("Percentage: ", percentage)
                style_function = lambda feature: {'fillColor': 'red', 'fillOpacity': 0.15 + (int(feature['properties']['total_cases'])/int(feature['properties']['country_total_cases'])), 'color': 'white', 'weight': 0.75}
                text = "<div><h5>" + city.name + "</h5><h6>Vaka Sayısı: " + str(int(city.total_cases)) \
                       + " (%{:.2f}) ".format(percentage)\
                       + "</h6><h6>Ölü Sayısı: " + str(int(city.total_deaths)) + "</h6><hr><h4>" + str(country.name)\
                       + "</h4><h5>Vaka Sayısı: " + str(int(country.total_cases)) + "</h5>" \
                       + "<h5>Ölü Sayısı: " + str(int(country.total_deaths)) + "</h5></div>"
                popup = folium.Popup(html=text, max_width=200, min_width=150, sticky=False)
                tooltip = folium.Tooltip(text=city.name)
                geoJsonLayer = folium.GeoJson(city_geojson, style_function=style_function, tooltip=tooltip)
                geoJsonLayer.add_child(popup)
                geoJsonLayer.add_to(il_feature_group)

                country_Circle.add_to(ulke_feature_group)
        else:
           country_Circle.add_to(m)

    item_txt = """<br> &nbsp; Vaka Sayısı: &nbsp; {total_cases} <br> &nbsp; Ölü Sayısı:  &nbsp; {total_deaths}"""
    html_itms = item_txt.format(total_cases=int(total_cases), total_deaths=int(total_deaths))

    legend_html = """
         <div style="
         position: fixed; 
         bottom: 25px; left: 25px;
         border:2px white; z-index:9999; 

         font-size:12px;
         font-weight: bold;
         background: white;
         color: #5f6769;
         opacity: 0.8;
         padding : 5px;
         ">
         <center><h5>{title}</h5></center>

         {itm_txt}

          </div> """.format(title="Dünya Geneli", itm_txt=html_itms)
    m.get_root().html.add_child(folium.Element(legend_html))

    il_feature_group.add_to(m)
    ulke_feature_group.add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)

    minimap = plugins.MiniMap(width=100, height=75, minimized=True, toggle_display=True)
    m.add_child(minimap)

    m.save(map_path)

    print("You can find map file at: ", os.path.join(os.getcwd(), map_path))

    # html_head = m.get_root().header.render()
    # html_body = m.get_root().html.render()
    # html_script = m.get_root().script.render()

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
        print("add_countries_to_database: ", row['CountryName'])
        cursor.execute(query)
        print()

    db.commit("add_countries_to_database: ", row['CountryName'])

def insert_countrydata_to_database():
    global countries, db
    cursor = db.cursor()

    for country in countries[1:]:
        check_query = 'select data_id from data where data_country = ' \
                      '(select country_id from country where country_name = "{v1}")'.format(v1=country.name)
        cursor.execute(check_query)
        check = cursor.fetchall()
        # print(check)
        if check == []:
            # print("{country} is not in the table named data. It will be added automatically.".format(country=country.name))
            add_country_to_data_query = 'insert into data("data_country", "data_total_cases", "data_new_cases", ' \
                                        '"data_total_deaths", "data_new_deaths", "data_total_recovered", ' \
                                        '"data_active_cases", "data_critical_cases", "data_tot_cases_per_1m", ' \
                                        '"data_tot_deaths_per_1m") ' \
                                        'values((select country_id from country where country_name = "{v1}"), {v2}, {v3}, {v4}, {v5}, {v6}, {v7}, {v8}, {v9}, {v10})'
            add_country_to_data_query = add_country_to_data_query.format(v1=country.name, v2=country.total_cases, v3=country.new_cases, v4=country.total_deaths,
                                                                         v5=country.new_deaths, v6=country.total_recovered, v7=country.active_cases,
                                                                         v8=country.critical_cases, v9=country.tot_cases_per_1m, v10=country.tot_deaths_per_1m)
            # print(add_country_to_data_query)
            cursor.execute(add_country_to_data_query)
            db.commit()
            print("(INSERT)insert_countrydata_to_database: ", country.name)
        else:
            # print("{country} is in the table named data. It's data will be updated.".format(country=country.name))
            update_country_query = 'update data set data_total_cases = {v2}, data_new_cases = {v3}, ' \
                                   'data_total_deaths = {v4}, data_new_deaths = {v5}, data_total_recovered={v6}, ' \
                                   'data_active_cases={v7}, data_critical_cases={v8}, data_tot_cases_per_1m={v9}, '\
                                   'data_tot_deaths_per_1m = {v10} '\
                                   'where data_country = (select country_id from country where country_name = "{v1}")'
            update_country_query = update_country_query.format(v1=country.name, v2=country.total_cases, v3=country.new_cases, v4=country.total_deaths,
                                                               v5=country.new_deaths, v6=country.total_recovered, v7=country.active_cases,
                                                               v8=country.critical_cases, v9=country.tot_cases_per_1m, v10=country.tot_deaths_per_1m)
            # print(update_country_query)
            cursor.execute(update_country_query)
            db.commit()
            print("(UPDATE)insert_countrydata_to_database: ", country.name)


if __name__ == "__main__":
    main()