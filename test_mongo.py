from pymongo import MongoClient
client = MongoClient('mongodb+srv://5techg1999:5TechG%40007@shockabsorber.ssvfzx6.mongodb.net/ShockAbsorber')
print(client.list_database_names())