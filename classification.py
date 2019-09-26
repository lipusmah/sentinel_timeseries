from slite_api import *



if __name__ == "__main__":
    conn = sqliteConnector(r"./dbs/raba_2018_susa.sqlite")
    api_create_tables(conn)

    RABE = [1100, 1160, 1180, 1190, 1300, 1321, 1211, 1212, 1221,
            1222, 1230, 1240, 1410, 1420, 1500, 1600, 1800, 2000]

    api_merge_temp_databases(conn, RABE)