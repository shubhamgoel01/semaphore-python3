import paramiko, getpass, datetime, os, subprocess, csv
from paramiko import SSHClient, AutoAddPolicy
from rich import print, pretty, inspect
from colorama import Fore, Back, Style, init
pretty.install()
client = SSHClient()
path = os.getcwd()
di = path+"/"+datetime.datetime.now().strftime("%D%H%M").replace('/','')
dirpath = "mkdir "+di
hostfile = path+"/hostname.txt"
os.system("clear")
csvfilename = di+"/"+datetime.datetime.now().strftime("%D%H%M").replace('/','')+".csv"
MaintinanceMode=False
#MaintinanceMode=True
ip = "10.20.48."
activelist=[]
print("................................. PanTerra Networks Operations DCW Raid Audit Script ",str(datetime.datetime.now()),"...............................\n ")


def csvwrite(person):
    try:
        #print(csvfilename)
        csvfile=open(csvfilename,'a', newline='')
        obj=csv.writer(csvfile)
        obj.writerows(person)
        csvfile.close()
    except Exception as e:
        print("Error: CSVwrite: ",str(e))

def filewrite(serverfile,Hostname,IPAddress,Mounts):
    try:
        file = open(serverfile,'w')
        file.write("Hostname : ")
        file.write(Hostname)
        file.write("IPAddress : ")
        file.write(IPAddress)
        file.write("Gluster Mount Points : \n")
        file.write(Mounts)
        file.close()
    except Exception as e:
        print("Error: Filewrite: ",str(e))

def find_nrpe_config():
    possible_paths = [
        "/usr/local/nagios/nrpe.cfg",
        "/etc/nagios/nrpe.cfg",
    ]

    for path in possible_paths:
        stdin, stdout, stderr = client.exec_command(f"test -f {path} && echo {path}")
        found_path = stdout.read().decode("utf8").strip()
        if found_path:
            return found_path
    return None

def RNSC():# Function to exceute shell command in the remote server or host and share the output data
    nrpe_path = find_nrpe_config()
    if not nrpe_path:
        print("NRPE config file not found in expected locations.")
        return "No"

    cmd = f'cat {nrpe_path} | grep -v "#" | grep -i raid.pl'
    stdin, stdout, stderr = client.exec_command(cmd)
    dout = stdout.read().decode("utf8")
    derr = stderr.read().decode("utf8")
    if(dout==""):
        print("raid.pl File not found in nrpe.cfg")
        return("No")
    else:
        cmd = (((dout.split('['))[1]).split(']'))[0]
        command="timeout -k 1 65 ngrep -n 1 -q -Wbyline "+cmd+" host 10.20.48.189 -d any"
        stdin, stdout, stderr = client.exec_command(command)
        Stdout=stdout.read().decode("utf8")
        Stderr=stderr.read().decode("utf8")
        if(Stdout==""):
            if(Stderr==""):
                return("No")
            else:
                dy = "Error: RNSC "+Stderr
                return(dy)
        if(Stdout!=""):
            if(Stderr==""):
                return("Yes")

def NRCC():#  Is RAID monitoring in Nagios
    nrpe_path = find_nrpe_config()
    if not nrpe_path:
        print(Fore.RED + "Nagios NRPE config not found.", Style.RESET_ALL)
        return "No"

    cmd = f'cat {nrpe_path} | grep -v "#" | grep -i raid.pl'
    stdin, stdout, stderr = client.exec_command(cmd)
    dout = stdout.read().decode("utf8")
    derr = stderr.read().decode("utf8")
    if(dout==""):
        di="Nagios monitoring for Raid not found in nrpe.cfg"# MSG:- Raid monitoring not found in Nagios configuration file
        print(Fore.RED + di,Style.RESET_ALL)
        return("No")
    elif(dout!=""):# No null data check
        lent=len(dout.split("\n"))
        if(lent==2):# this condition only checks for one match
            if(dout[0]=="#"):
                di="Nagios Monitoring for Raid is disabled"# MSG:- Raid  is available in nagios but not enabled
                print(Fore.RED + di,Style.RESET_ALL)
                return("No")
            else:
                return("Yes")
        else:
            di="Duplicat Config found in nrpe.cfg"
            print(Fore.RED + di,Style.RESET_ALL)
            return("No")

def crontab(serverip):
    stdin, stdout, stderr = client.exec_command('crontab -l | grep -v "#" | grep raid_status.sh')
    data = stdout.read().decode("utf8")
    if(data==""):
        return("No")
    if(data!=""):# No null data check
        lent=len(data.split("\n"))
        if(lent==2):# this condition only checks if one cronjob is defined in the
            if( data[0]=="#"):
                return("No")
            else:# Raid cron job is enabled, we will check for status of the disk is Optimal or Degraded
                cronjobid1=data.split(" ")[5]
                subcmd = "cat "+cronjobid1.split("\n")[0]+" | grep 'Subject'"
                #print(subcmd)
                stdin, stdout, stderr = client.exec_command(subcmd)
                subject = stdout.read().decode("utf8").split("xx.xx.")[1].split("\n")[0]
                #print(subject)
#                print("Script IP Address : ",subject)
                if(subject==serverip.split(".")[3]):
                    print("IP Matched in Crobtab Script            : ",Fore.GREEN + "Yes",Style.RESET_ALL)
                else:
                    print("IP Matched in Crontab Script            : ",Fore.RED + "No",Style.RESET_ALL)
                return("Yes")
        else:
            return("No")#Duplicat Cronjob found

def find_check_mega_raid():
    """Searches for the `check_mega_raid.pl` script in multiple known paths."""
    possible_paths = [
        "/usr/local/nagios/libexec/check_mega_raid.pl",
        "/usr/lib64/nagios/plugins/check_mega_raid.pl",
        "/usr/lib/nagios/plugins/check_mega_raid.pl",
    ]

    for path in possible_paths:
        stdin, stdout, stderr = client.exec_command(f"test -f {path} && echo {path}")
        found_path = stdout.read().decode("utf8").strip()
        if found_path:
            return found_path
    return None

def Audit(IP_Address,Hardware,Crontab,Nagios,Nagios_Server):
    RAID_Script=""
    raid_script_paths = [
    "/usr/local/nagios/libexec/check_mega_raid.pl",
    "/usr/lib64/nagios/plugins/check_mega_raid.pl",
    "/usr/lib/nagios/plugins/check_mega_raid.pl",
    ]
    # Find the correct path
    script_path = None
    for path in raid_script_paths:
        stdin, stdout, stderr = client.exec_command(f"ls {path}")
        if not stderr.read().decode("utf8"):
            script_path = path
            break
    if not script_path:
        print(Fore.RED + "RAID monitoring script not found in expected locations." + Style.RESET_ALL)
        return

    if(Crontab=="Yes"):
        stdin, stdout, stderr = client.exec_command("crontab -l | grep -v '#' | grep raid_status*")
        data = stdout.read().decode("utf8")
        stdin, stdout, stderr = client.exec_command(f"ls {script_path}")#  Audit starts
        if(stderr.read().decode("utf8")==""):# check for no error in command execuation
            data = data.split("\n")
            l=len(data)
            for i in range(0,l-1):
            #    print(data[i])
                stdin, stdout, stderr = client.exec_command("cat "+str(((data[i].split("\n"))[0].split())[5])+" | grep DETAILREPORT=")
                stdin, stdout, stderr = client.exec_command(((stdout.read().decode("utf8")).split("`"))[1]+" | grep -e 'State :' -e 'State               :'")
                dy=stdout.read().decode("utf8").replace("\n"," ")#  Filter Optimal from the data: error if other than Optimal
                #print("RAID Status of Script       : ",(((data[i].split())[5].split("/"))[4].split(".sh"))[0].replace("raid_status","Raid"),(dy.split(":"))[1])
                dy=(dy.split(":"))[1]
                if(dy == "clean" or "Optimal" or "active"):
                    print("RAID Status of Script       : ",(((data[i].split())[5].split("/"))[4].split(".sh"))[0].replace("raid_status","Raid"),Fore.GREEN + dy,Style.RESET_ALL)
                else:
                    print("RAID Status of Script       : ",(((data[i].split())[5].split("/"))[4].split(".sh"))[0].replace("raid_status","Raid"),Fore.RED + dy,Style.RESET_ALL)
                if(i==0):
                    RAID_Script=RAID_Script+(((data[i].split())[5].split("/"))[4].split(".sh"))[0].replace("raid_status","Raid")+dy
                else:
                    RAID_Script=RAID_Script+"\n"+(((data[i].split())[5].split("/"))[4].split(".sh"))[0].replace("raid_status","Raid")+dy

        else:
            di="File Not available"#MSG:-
            print(Fore.RED + di,Style.RESET_ALL)
    RAID_Nagios_Script=""
    if(Nagios=="Yes"):
        if not script_path:  # Ensure the script path was found earlier
            print(Fore.RED + "Nagios RAID monitoring script not found in expected locations." + Style.RESET_ALL)
            return

        # Execute the script with the appropriate interpreter (Perl in this case)
        stdin, stdout, stderr = client.exec_command(f"perl {script_path}")
        RAID_Nagios_Script = stdout.read().decode("utf8").replace(",", "-")
        person=[(IP_Address,Hardware,Crontab,Nagios,Nagios_Server,RAID_Script,RAID_Nagios_Script)]
        csvwrite(person)
        #print(person)
        tey= [(RAID_Nagios_Script)]
#        print(tey)
        dti = RAID_Nagios_Script.split(":")
        if(dti[0]=="OK"):#All Volumes/Disks are Optimal
            print("RAID Status of Nagios Script: ",Fore.GREEN + "OK",Style.RESET_ALL)
            print(tey)
        else:# MSG:- Found a issue with Volumes or disk
            print("RAID Status of Nagios Script: ",Fore.RED + "Check",Style.RESET_ALL)
            print(tey)
def sshclient(server,user,password):
    client.load_host_keys('/root/.ssh/known_hosts')
#    client.load_host_keys('/home/share/vrama/.ssh/known_hosts')
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(server,username=user, password = password)
    stdin, stdout, stderr = client.exec_command("/sbin/dmidecode | grep VMware")
    Hostname = stdout.read().decode("utf8")
    if not Hostname:
        stdin, stdout, stderr = client.exec_command("/sbin/dmidecode | grep 'Product Name'")
        output = stdout.read().decode("utf8").strip()

        # Extract product name
        c = ["", ""]  # Initialize c as a list to match original code structure
        for line in output.split("\n"):
            if "Product Name:" in line:
                c = line.split(":", 1)  # Keep it as a list like the original code
                c[1] = c[1].strip()  # Ensure proper formatting

        # Ignore "Standard PC" and proceed with others
        if len(c) > 1 and "Standard PC" not in c[1]:
            init(convert=True)
            di="Server IP: "+server
            print(di)
            print("Server H/W: ",c[1])
            print("")
            print("checking MegaRAID script enabled in Nagios Server:")
            print("-------------------------------------------------")
            cront=crontab(server)# Yes/No
            if(cront=="Yes"):
                print("RAID Script Enabled in Crontab          : ",Fore.GREEN + cront,Style.RESET_ALL)
            else:
                print("RAID Script Enabled in Crontab          : ",Fore.RED + cront,Style.RESET_ALL)
            nrcc=NRCC()#Yes/No
            if(nrcc=="Yes"):
                print("Is RAID monitoring in Nagios            : ",Fore.GREEN + nrcc,Style.RESET_ALL)
            else:
                print("Is RAID monitoring in Nagios            : ",Fore.RED + nrcc,Style.RESET_ALL)
            rnss=RNSC()#Yes/No
            if(rnss=="Yes"):
                print("MegaRAID script enabled in Nagios Server: ",Fore.GREEN + rnss, Style.RESET_ALL)
            else:
                print("MegaRAID script enabled in Nagios Server: ",Fore.RED + rnss, Style.RESET_ALL)
                print("")
            if(cront=="Yes" or nrcc=="Yes"):
                print("performing RAID audit. Validating RAID Script and RAID Nagios Plug-in output of the server:")
                print("------------------------------------------------------------------------------------------")
                Audit(server,c[1],cront,nrcc,rnss)
            else:
                person=[(server,c[1],cront,nrcc,rnss)]
                csvwrite(person)
            print("-----------------------------------------------------------------------------------------------------------------------\n\n")
        else:
            #print("VMware")
            person=[(server,"This is a VMWare Server (VM)")]
            csvwrite(person)

data = "Enter root password :"
password = getpass.getpass(data)
os.system(dirpath)
person=[("IP Address","Hardware","Crontab","Nagios","Nagios Server","RAID Script","RAID Nagios Script")]
csvwrite(person)

# Maintinance Mode :- Where we can run audit for particular IP's Mentioned in the hostname.txt file.
if(MaintinanceMode==True):
    print("Disabled Network scan, ACTIVATED MAINTENANCE MODE.")
    hostname = open(hostfile,'r')
    #os.system(dirpath)
    for i in hostname:
        IP=" ".join((i.strip('\n')).split(" "))
        if((IP[0]!="#") and (len(IP.split("."))==4)):
            print("IP: ",IP)
            activelist.append(IP)
    hostname.close()
    print(activelist)

if(MaintinanceMode==False):
    print("Scanning Network",end="")
    for i in range (1,255):
        print(".",end="")
        cmd = "ping -c 1 "+ip+str(i)
        resp=os.popen(cmd)
        data = resp.readlines()
        if(data[1].count("ttl")):
            activelist.append(ip+str(i))
        else:
            person=[(ip+str(i),"IP Address is not in use")]
            csvwrite(person)

#print(activelist) # All the IP Address list which are assigned

print("")
for i in activelist:
    try:
        #print(i)
        sshclient(i,"root",password)
    except Exception as e:
        print("Error: ssh ",i.strip('\n'),str(e))
        if(str(e)=="Authentication failed."):
            person=[(i.strip('\n'),"Unable to Login using our credentials")]
            csvwrite(person)
        elif(str(e)=="Bad authentication type; allowed types: ['publickey', 'keyboard-interactive']"):
            person=[(i.strip('\n'),"Is a ESXi Server")]
            csvwrite(person)
        elif(i.strip('\n')=="10.20.48.168"):
            person=[(i.strip('\n'),"It's NAT/PAT IP used in Barracuda for Gateway")]
            csvwrite(person)
        else:
            person=[(i.strip('\n'),str(e))]
            csvwrite(person)

#hostname.close()
print("**Completed**")
print("-------------")
