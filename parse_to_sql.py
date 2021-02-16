import sqlite3
import os

# Values
config_dir = 'Configs'
used_config_dir = 'UsedConfigs'
db_file = 'test.db'

# Open connect to DataBase
def sql_connect(db_file_name):
    try:
        db_connect = sqlite3.connect(db_file_name)
        return db_connect
    except sqlite3.Error:
        print(sqlite3.Error)

# Create tables at DB if not exists
def sql_create_table(db_connect):
    db_cursor = db_connect.cursor()
    db_cursor.execute("CREATE TABLE if not exists Devices (device_id integer not NULL PRIMARY KEY, hostname text, type text, vendor text, model text, sw_version text, functions text, location text, auth text, segment text, cluster text, admin_fio text, config_name text)")
    db_cursor.execute("CREATE TABLE if not exists Interfaces (interface_id integer not NULL PRIMARY KEY, name text, ip text, mask text, desc text, vrf text, status integer, access_vlan text, tagged_vlan text, device_id integer not null)")
    db_connect.commit()

# Insert data in DB
def sql_insert_date(db_connect,rows,file_name):
    db_cursor = db_connect.cursor()
    # Insert to Devices table
    command = str('INSERT INTO Devices (hostname,sw_version,config_name,cluster,location,vendor,auth,type) VALUES (\'' + str(rows['hostname']) + '\',\'' + str(rows['sw_file']) + '\',\'' + str(file_name) + '\',\'' + str(rows['cluster']) + '\',\'' + str(rows['location']) + '\',\'' + str(rows['vendor']) + '\',\'' + str(rows['auth']) + '\',\'' + str(rows['type']) + '\')')
    #print(command)
    db_cursor.execute(command)
    db_connect.commit()
    # Get device id
    command = 'SELECT device_id FROM Devices where config_name = \'' + file_name + '\''
    #print(command)
    db_cursor.execute(command)
    device_id = db_cursor.fetchall()[0][0]
    # Insert to Interfaces table
    for i in rows['interfaces']:
        command = 'INSERT INTO Interfaces (name,desc,ip,mask,vrf,status,access_vlan,tagged_vlan,device_id) VALUES (\'' + str(i['name']) + "\',\'" + str(i['desc']) + "\',\'" + str(i['ip']) + "\',\'" + str(i['mask']) + "\',\'" + str(i['vrf']) + "\',\'" + str(i['status']) + "\',\'" + str(i['access_vlan']) + "\',\'" + str(i['tagged_vlan']) + "\',\'" + str(device_id) + '\')'
        #print(command)
        db_cursor.execute(command)
        db_connect.commit()

# Get file list in directory with configs
def list_files_in_dir(dir):
    file_list = os.listdir(dir)
    return(file_list)

def parse_config_files (config_dir,file):
    device_dict = dict()
    device_dict['interfaces'] = list()
    device_dict['cluster'] = 0
    device_dict['sw_file'] = 'N/A'
    device_dict['location'] = 'N/A'
    device_dict['type'] = 'N/A'
    with open(config_dir + '/' + file) as file:
        # Create list in list from config
        config = file.readlines()
        config_list = list()
        for i in config:
            config_list.append(i.split(" "))
        # Search in list
        config_list_len = len(config_list)
        i = 0
        iface = 0
        while i < config_list_len:
            if config_list[i][0] == 'hostname':
                device_dict['hostname'] = str(config_list[i][1]).strip('\n')
            elif config_list[i][0].strip('\n') == 'redundancy':
                device_dict['type'] = 'Router'
            elif config_list[i][0] == 'spanning-tree':
                device_dict['type'] = 'SW'
            elif config_list[i][0] == 'switch':
                device_dict['cluster'] = 1
            elif config_list[i][0] == 'snmp-server':
                if config_list[i][1] == 'location':
                    device_dict['location'] = str(config_list[i][2]).strip('\n')
            elif config_list[i][0] == 'boot':
                if config_list[i][1] == 'system':
                    device_dict['sw_file'] = str(config_list[i][3]).strip('\n')
            elif config_list[i][0] == 'interface':
                device_dict['interfaces'].append(dict())
                device_dict['interfaces'][iface]['name'] = config_list[i][1].strip('\n')
                device_dict['interfaces'][iface]['status'] = 1
                device_dict['interfaces'][iface]['desc'] = ''
                device_dict['interfaces'][iface]['ip'] = ''
                device_dict['interfaces'][iface]['mask'] = ''
                device_dict['interfaces'][iface]['vrf'] = ''
                device_dict['interfaces'][iface]['access_vlan'] = 1
                device_dict['interfaces'][iface]['tagged_vlan'] = 'none'
                i2 = i + 1
                while config_list[i2][0] == '':
                    #print(config_list[i2])
                    if config_list[i2][1] == 'description':
                        device_dict['interfaces'][iface]['desc'] = " ".join(config_list[i2][2:]).strip('\n').strip('*')
                    elif config_list[i2][1] == 'encapsulation':
                        if config_list[i2][2] == 'dot1Q':
                            device_dict['interfaces'][iface]['tagged_vlan'] = config_list[i2][3].strip('\n')
                    elif config_list[i2][1] == 'switchport':
                        if config_list[i2][2] == 'access':
                            device_dict['interfaces'][iface]['access_vlan'] = config_list[i2][4].strip('\n')
                        elif config_list[i2][2] == 'trunk':
                            if config_list[i2][3] == 'allowed':
                                device_dict['interfaces'][iface]['tagged_vlan'] = config_list[i2][5].strip('\n')
                    elif config_list[i2][1].strip('\n') == 'shutdown':
                        device_dict['interfaces'][iface]['status'] = 0
                    elif config_list[i2][1] == 'ip':
                        if config_list[i2][2] == 'address':
                            device_dict['interfaces'][iface]['ip'] = "".join(config_list[i2][3]).strip('\n')
                            device_dict['interfaces'][iface]['mask'] = "".join(config_list[i2][4]).strip('\n')
                        elif config_list[i2][2] == 'vrf':
                            device_dict['interfaces'][iface]['vrf'] = "".join(config_list[i2][4]).strip('\n')
                    i2 += 1
                #print('-------')
                iface += 1
            i += 1
        return device_dict

# Main function
config_files = list_files_in_dir(config_dir)

# Open DB and create tables if not exists
db_connect = sql_connect(db_file)
sql_create_table(db_connect)

#
for file_name in config_files:
    # Parse configs
    device = parse_config_files(config_dir,file_name)
    device['vendor'] = 'Cisco'
    device['auth'] = 'local'
    # Insert data to DB
    sql_insert_date(db_connect,device,file_name)
    # Move parsed config in archived config dir
    os.replace(config_dir+'/'+file_name,used_config_dir+'/'+file_name)

# Close DB
db_connect.close()