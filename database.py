import pymongo


class MongoConnect:
    def __init__(self):
        connection = pymongo.MongoClient('localhost', 27017)
        # if db_name in connection.list_database_names():
        #     print("The database exists\nConnecting...")
        self.db = connection["db"]
        self.coll = self.db["coll"]
        self.donate_coll = self.db["donated"]
