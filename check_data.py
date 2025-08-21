from pymongo import MongoClient
client = MongoClient('mongodb+srv://5techg1999:5TechG%40007@shockabsorber.ssvfzx6.mongodb.net/ShockAbsorber')
db = client['ShockAbsorber']
print(list(db['absorbers'].find({}, {'_id': 0})))