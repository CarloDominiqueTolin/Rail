import pymongo
import csv
from datetime import datetime
from support_funcs import getCurentLoc
from zipfile import ZipFile 
from bson import ObjectId
import os
import csv

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

DB_NAME = 'rail_crack_db'
ROW_TEMP = { "name": "John", "address": "Highway 37" }
mydb = myclient['rail_crack_db']
mycol = mydb['cracks']



def getAllDetections(column=None):
    if type(column)==str:
        return [{'id':str(x['_id']),column:x[column]} for x in mycol.find().sort("timestamp")]
    else:
        return [x for x in mycol.find().sort("timestamp")]



def insertDetection(timestamp,image_file,detections,location):
    x = mycol.insert_one({
        'timestamp':timestamp,
        'image_file':image_file,
        'detections':detections,
        'locations':location
    })
    print(f'Record inserted at {x}')



def deleteByID(id):
    image_file = mycol.find_one(ObjectId(id))['image_file']
    os.remove(image_file)
    try:
        mycol.delete_one({"_id":ObjectId(id)})
        print(f"Record ID {id} deleted")
    except Exception as e:
        print(f"An error occurred: {e}")



def getAllCoordinates():
    records = mycol.find({}, {"_id": 1, "detections": 1, "locations": 1})

    result = []
    for record in records:
        has_detections = bool(record.get("detections"))
        
        result.append({
            "id": str(record["_id"]),
            "has_detections": has_detections,
            "locations": record.get("locations"),
        })
    
    return result



def export_to_csv(output_file='download/rail_cracks.csv', start_date=None, end_date=None, cracks=None):
    # Build the query
    query = {}

    # Filter by date range
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            query["timestamp"]["$lte"] = datetime.strptime(end_date, "%Y-%m-%d")

    if cracks is not None:
        if cracks:  # Records with cracks
            query["detections.Crack"] = {"$gt": 0}
        else:  # Records with no cracks
            query["detections.Crack"] = {"$exists": False}

    records = mycol.find(query)

    with open(output_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Timestamp", "Image File", "Detections", "Location"])
        for record in records:
            writer.writerow([
                str(record["_id"]),
                record["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                record["image_file"].split('/')[-1],
                "; ".join(f"{k}: {v}" for k, v in record["detections"].items()),
                f"{record['locations'][0]}, {record['locations'][1]}",
            ])

    print(f"Data successfully exported to {output_file}")

    image_files = []
    with open(output_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            image_files.append(row["Image File"])

    with ZipFile(f'{output_file.split('.')[0]}.zip','w') as zip: 
        zip.write(output_file, output_file.split('/')[-1])
        for file in image_files: 
            zip.write(f'assets/db/{file}', file) 
  
    print('All files zipped successfully!')  




if __name__=='__main__':
    export_to_csv()

