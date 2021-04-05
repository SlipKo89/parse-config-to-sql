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
        print("Connect to DB - OK")
        return db_connect
    except sqlite3.Error:
        print(sqlite3.Error)

# Create tables at DB if not exists
def sql_create_table(db_connect):
    db_cursor = db_connect.cursor()
    db_cursor.execute("CREATE TABLE if not exists Devices (device_id integer not NULL PRIMARY KEY, hostname text, type text, vendor text, model text, sw_version text, functions text, location text, auth text, segment text, cluster text, admin_fio text, config_name text, uptime text, sum_ifaces text)")
    db_cursor.execute("CREATE TABLE if not exists Interfaces (interface_id integer not NULL PRIMARY KEY, name text, ip text, mask text, desc text, vrf text, status integer, access_vlan text, tagged_vlan text, device_id integer not null)")
    db_cursor.execute("CREATE TABLE if not exists Vlans (vlan_id integer not NULL PRIMARY KEY, vid text, name text, device_id integer not null)")
    db_cursor.execute("CREATE VIEW if not exists test as SELECT dev.hostname,dev.type,dev.vendor,dev.model,dev.sw_version,dev.functions,dev.location,dev.auth,dev.segment,dev.cluster,dev.admin_fio,dev.config_name, dev.sum_ifaces, ifc.name,ifc.ip,ifc.mask,ifc.desc,ifc.vrf,ifc.status,ifc.access_vlan,ifc.tagged_vlan from Devices as dev,Interfaces as ifc where dev.device_id = ifc.device_id ORDER by dev.hostname")
    db_connect.commit()
    print("Created tables DB - OK")

# Insert data in DB
def sql_insert_date(db_connect,rows,file_name):
    print("Begin insert to DB")
    db_cursor = db_connect.cursor()
    # Insert to Devices table
    command = "INSERT INTO Devices (hostname,sw_version,config_name,cluster,location,vendor,auth,type,model,uptime,sum_ifaces) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
    val = (str(rows['hostname']),str(rows['sw_file']),str(file_name),str(rows['cluster']),str(rows['location']),str(rows['vendor']),str(rows['auth']),str(rows['type']),str(rows['model']),str(rows['uptime']),str(rows['sum_ifaces']))
    #print(command,val)
    db_cursor.execute(command,val)
    db_connect.commit()

    # Get device id
    command = 'SELECT device_id FROM Devices where config_name = \'' + file_name + '\''
    db_cursor.execute(command)
    device_id = db_cursor.fetchall()[0][0]

    # Insert to Vlans table
    for i in rows['vlan']:
        command = 'INSERT INTO Vlans (vid,name,device_id) VALUES (?,?,?)'
        val = (str(i), str(rows['vlan'][i]), str(device_id))
        #print(val)
        db_cursor.execute(command, val)
        #db_connect.commit()

    # Check 2 "sh run" outputs in file
    rows_len = len(rows['interfaces'])
    print("Detect " + str(rows['flag_2_sh_run']) + " sh run output")
    if rows['flag_2_sh_run'] == 2:
        rows_len = rows_len / 2

    # Insert to Interfaces table
    a = 0
    for i in rows['interfaces']:
        if a < rows_len:
            command = 'INSERT INTO Interfaces (name,desc,ip,mask,vrf,status,access_vlan,tagged_vlan,device_id) VALUES (?,?,?,?,?,?,?,?,?)'
            val = (str(i['name']),str(i['desc']),str(i['ip']),str(i['mask']),str(i['vrf']),str(i['status']),str(i['access_vlan']),str(i['tagged_vlan']),str(device_id))
            #print(command)
            db_cursor.execute(command,val)
            db_connect.commit()
            a += 1
    print("End Insert to DB")

# Get file list in directory with configs
def list_files_in_dir(dir):
    file_list = os.listdir(dir)
    #print(file_list)
    return(file_list)

# Parse config file
def parse_config_files (config_dir,file):
    print("Start parse config file")
    # Init device dict
    device_dict = dict()
    device_dict['interfaces'] = list()
    device_dict['cluster'] = 0
    device_dict['sw_file'] = 'N/A'
    device_dict['location'] = 'N/A'
    device_dict['type'] = 'N/A'
    device_dict['model'] = 'N/A'
    device_dict['flag_2_sh_run'] = 0
    device_dict['vlan'] = dict()
    device_dict['uptime'] = 'N/A'
    device_dict['sum_ifaces'] = 'N/A'

    # Open config file for parsing
    with open(config_dir + '/' + file) as file:
        # Create list in list from config
        config = file.readlines()
        config_list = list()
        for i in config:
            config_list.append(i.split(" "))

        # Search hostname in list
        config_list_len = len(config_list)
        i = 0
        while i < config_list_len:
            if config_list[i][0] == 'hostname':
                device_dict['hostname'] = str(config_list[i][1]).strip('\n')
                hostname = str(config_list[i][1]).strip('\n')
            i += 1

        # Search other atributes in list
        i = 0
        iface = 0
        while i < config_list_len:

            #Detect 2sh run
            if config_list[i][0] == str(hostname + "#sh"):
                if config_list[i][1].strip("\n") == 'run':
                    #print(config_list[i])
                    device_dict['flag_2_sh_run'] += 1
            if config_list[i][0] == '------------------':
                if config_list[i][1] == 'show':
                    if config_list[i][2] == 'running-config':
                        #print (config_list[i])
                        device_dict['flag_2_sh_run'] += 1

                    # Detect vlan
                    elif config_list[i][2] == 'vlan':
                        vlan_i = i + 6
                        while config_list[vlan_i][0] != '\n':
                            #print(config_list[vlan_i])
                            if config_list[vlan_i][0].strip('\n') != '':
                                vlan = str(config_list[vlan_i][0].strip('\n'))
                                if len(vlan) == 1:
                                    vlan_name = str(config_list[vlan_i][4])
                                elif len(vlan) == 2:
                                    vlan_name = str(config_list[vlan_i][3])
                                elif len(vlan) == 3:
                                    vlan_name = str(config_list[vlan_i][2])
                                elif len(vlan) == 4:
                                    vlan_name = str(config_list[vlan_i][1])
                                device_dict['vlan'][vlan] = vlan_name
                            vlan_i += 1

            # Detect router
            elif config_list[i][0].strip('\n') == 'redundancy':
                if device_dict['type'] == 'N/A':
                    device_dict['type'] = 'Router'
            # Detect switch
            elif config_list[i][0] == 'spanning-tree':
                device_dict['type'] = 'SW'
            # Detect switch numbers
            elif config_list[i][0] == 'switch':
                device_dict['cluster'] = config_list[i][1]
            # Detect Locations from SNMP
            elif config_list[i][0] == 'snmp-server':
                if config_list[i][1] == 'location':
                    device_dict['location'] = str(config_list[i][2]).strip('\n')
            # Detect System Software version
            elif config_list[i][0] == 'System':
                if config_list[i][1] == 'image':
                    if config_list[i][2] == 'file':
                        device_dict['sw_file'] = str(config_list[i][4]).strip('\n')
            # Detect model
            elif config_list[i][0] == 'Processor':
                if config_list[i][1] == 'board':
                    device_dict['model'] = config_list[i-1][1]
                    #print(config_list[i-1][1])

                    # Get interfaces summary info
                    ifce_i = i + 1
                    sum_ifaces = str()
                    while config_list[ifce_i][0] != '\n' and (config_list[ifce_i][-1].strip('\n') == 'interface' or config_list[ifce_i][-1].strip('\n') == 'interfaces' or config_list[ifce_i][-1].strip('\n') == 'interface(s)' or config_list[ifce_i][-1].strip('\n') == 'port' or config_list[ifce_i][-1].strip('\n') == 'ports' or config_list[ifce_i][-1].strip('\n') == 'port(s)'):
                    #    print(config_list[ifce_i])
                        sum_ifaces = sum_ifaces + str(" ".join(config_list[ifce_i]).strip('\n')) + str(", ")
                        ifce_i += 1
                    device_dict['sum_ifaces'] = sum_ifaces

            # Detect uptime
            elif config_list[i][0] == hostname:
                if config_list[i][1] == 'uptime':
                    #print (" ".join(config_list[i][3:]))
                    device_dict['uptime'] = " ".join(config_list[i][3:]).strip('\n')
            # Detect Interfaces
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
                    # Detect Description
                    if config_list[i2][1] == 'description':
                        device_dict['interfaces'][iface]['desc'] = " ".join(config_list[i2][2:]).strip('\n').strip('*').strip("\'")
                    # Detect vlan for routers
                    elif config_list[i2][1] == 'encapsulation':
                        if config_list[i2][2] == 'dot1Q':
                            device_dict['interfaces'][iface]['tagged_vlan'] = config_list[i2][3].strip('\n')
                    # Detect vlan for switches
                    elif config_list[i2][1] == 'switchport':
                        if config_list[i2][2] == 'access':
                            device_dict['interfaces'][iface]['access_vlan'] = config_list[i2][4].strip('\n')
                        elif config_list[i2][2] == 'trunk':
                            if config_list[i2][3] == 'allowed':
                                device_dict['interfaces'][iface]['tagged_vlan'] = config_list[i2][5].strip('\n')
                    # Detect adm status for interface
                    elif config_list[i2][1].strip('\n') == 'shutdown':
                        device_dict['interfaces'][iface]['status'] = 0
                    # Detect vrf
                    elif config_list[i2][1].strip('\n') == 'vrf':
                        device_dict['interfaces'][iface]['vrf'] = "".join(config_list[i2][3]).strip('\n')
                    # Detect for address and vrf
                    elif config_list[i2][1] == 'ip':
                        if config_list[i2][2] == 'address':
                            device_dict['interfaces'][iface]['ip'] = "".join(config_list[i2][3]).strip('\n')
                            device_dict['interfaces'][iface]['mask'] = "".join(config_list[i2][4]).strip('\n')
                        elif config_list[i2][2] == 'vrf':
                            device_dict['interfaces'][iface]['vrf'] = "".join(config_list[i2][4]).strip('\n')
                    # increment for interface cycle
                    i2 += 1
                iface += 1
            i += 1
        print('End Parse config file')
        return device_dict

# Main function
config_files = list_files_in_dir(config_dir)

# Open DB and create tables if not exists
db_connect = sql_connect(db_file)
sql_create_table(db_connect)

# Parse and insert to db for config files
for file_name in config_files:
    print ("Start ",file_name,"\n----------------------------------")
    # Parse configs
    device = parse_config_files(config_dir,file_name)
    device['vendor'] = 'Cisco'
    device['auth'] = 'local'
    # Insert data to DB
    sql_insert_date(db_connect,device,file_name)
    # Move parsed config in archived config dir
    os.replace(config_dir+'/'+file_name,used_config_dir+'/'+file_name)
    print(device['uptime'])

# Close DB
db_connect.close()

print("----------------------------------\nFinish! Goodbuy")