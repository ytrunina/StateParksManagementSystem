import random
import urllib.request, urllib.parse, urllib.error, json, mysql.connector

mydb = mysql.connector.connect(
    host="db-stateparks.c50qqk98cxr9.us-east-1.rds.amazonaws.com",
    user="connectadmin",
    password="EWCfglgz9",
    database="StateParks_TEST"
)

endpoint = "https://developer.nps.gov/api/v1/parks?stateCode=fl"
HEADERS = {"X-Api-Key":"ipex52YflkWmNNHpmNRWl8KKCUHeNp9hgGGfEInY"}
req = urllib.request.Request(endpoint, headers=HEADERS, method = "GET")

# to time the process in windows: Measure-Command {python3 test.py}
# to time the process in mac/linux: time python3 test.py

# show that this script runs once, then a few more times to show that it properly updates the database

with urllib.request.urlopen(req) as response:
    response_data = response.read().decode('utf-8')
    NPS_parks_data = json.loads(response_data)
    NPS_parks_data.pop('limit', None)
    for park in NPS_parks_data['data']:
        park.pop('id', None)
        park.pop('activities', None)
        park.pop('topics', None)
        park.pop('parkCode', None)
        park.pop('latitude', None)
        park.pop('longitude', None)
        park.pop('latLong', None)
        park.pop('states', None)
        park.pop('contacts', None)
        park.pop('operatingHours', None)
        park.pop('entranceFees', None)
        
        park['isRandom'] = False

        if len(park["entrancePasses"]) > 1:
            park["entrancePasses"] = park["entrancePasses"][:1]
        elif len(park["entrancePasses"]) == 0:
            # if they don't sell entrance passes, create one and give it a random number between [20, 40] in intervals of 2
            park["entrancePasses"] = [{"cost": str(random.randrange(20, 40, 2)) + ".00"}]
            park['isRandom'] = True

        cost = 0

        for entrancePass in park['entrancePasses']:
            # if the cost is 0.00, give it a random number between [20, 40] in intervals of 2
            if entrancePass['cost'] == '0.00':
                entrancePass['cost'] = str(random.randrange(20, 40, 2)) + ".00"
                park['isRandom'] = True

            cost = entrancePass['cost']

            entrancePass.pop('description', None)
            entrancePass.pop('title', None)

        park.pop('entrancePasses', None)
        park['cost'] = cost

        addressStr = ""
        # pop lines 3 and 2 of addresses
        for address in park['addresses']:
            address.pop('line3', None)
            address.pop('line2', None)
            # if the type is 'Mailing', pop it from the list
            if address['type'] == 'Mailing':
                park['addresses'].remove(address)
            address.pop('type', None)
            
            # create new string with the address in this format: Street, City, State, Zip
            addressStr = address['line1'] + ", " + address['city'] + ", " + address['stateCode'] + ", " + address['postalCode']

        park.pop('addresses', None)        
        park['address'] = addressStr

        park.pop('fees', None)
        park.pop('directionsInfo', None)
        park.pop('directionsUrl', None)
        park.pop('images', None)
        park.pop('designation', None)
        park.pop('name', None)
        park.pop('weatherInfo', None)

    # write to json file
    #with open('parks.json', 'w') as outfile:
        #json.dump(NPS_parks_data, outfile, indent=4)

    with mydb.cursor() as cur:
        # table name: StateParks table
        # fields: name, description, price, url, address, isActive
        for park in NPS_parks_data['data']:
            try:
                # If the park already exists get the id (priamry key)
                cur.execute("SELECT id FROM StateParks WHERE name LIKE %s", (park['fullName'],))
                park_id = cur.fetchone()

                if park_id:
                    # If it exists and a random number was generated, update everything BUT the price
                    # Else if exists and price was taken from API, update ALL
                    if park['isRandom']:
                        sql = "UPDATE StateParks SET description = %s, url = %s, address = %s WHERE name LIKE %s"
                        val = (park['description'], park['url'], park['address'], park['fullName'])
                    else:
                        sql = "UPDATE StateParks SET description = %s, url = %s, address = %s, price = %s WHERE name LIKE %s"
                        val = (park['description'], park['url'], park['address'], float(park['cost']), park['fullName'])
                else:
                    # If doesnt exist in database, insert into it
                    sql = "INSERT INTO StateParks (name, description, price, url, address, isActive) VALUES (%s, %s, %s, %s, %s, %s)"
                    val = (park['fullName'], park['description'], float(park['cost']), park['url'], park['address'], 1)

                cur.execute(sql, val)
                mydb.commit()
                print("Query execution succeeded")
            except Exception as e:
                print("Query execution failed. Error: " + str(e))
                mydb.rollback()

        cur.close()
    
