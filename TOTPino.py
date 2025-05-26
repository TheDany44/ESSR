#sudo python3 script.py

import os
import subprocess
import difflib
import sys

def read_file(filename):
    secrets = []
    plats = []
    with open(filename, 'r') as file:
        for line in file:
            line.strip()  # Removes the newline character
            try:
                c_secret, c_plat = line.split('-')
            except:
                continue
            secrets.append(c_secret.replace('\n', ''))
            plats.append(c_plat.replace('\n', ''))

    return secrets, plats

#vuur2fim7ri3f7ku5xid4754lsz3qeir-SecretDB
def write_file(filename, secrets, plats):

    if(len(plats)==0):
        with open(filename, 'w') as file:
            file.write()
        return
    
    lines = []

    for i in range(len(plats)):
        line = secrets[i]+"-"+plats[i]
        lines.append(line)
    
    with open(filename, 'w') as file:
        for line in lines:
            file.write(line + '\n')



def insert_secret(filename):
    secrets,plats = read_file(filename)
    flag = 0
    if (len(plats) == 6):
        print(f"\n\nYou already have {len(plats)}/6 secrets")
        flag=1
    else:
        print(f"\n\nYou have {len(plats)}/6 secrets")
    
    if(len(plats) != 0):
        print("The identifiers you chose are:")
        for i in plats:
            print("-> "+i)
    
    if(flag):
        return

    n_secret = input("Insert the new secret: ")
    n_plat = input("Insert the new identifier:" )

    secrets.append(n_secret)
    plats.append(n_plat)
    return write_file(filename, secrets, plats)


def remove_secret(filename):
    secrets,plats = read_file(filename)

    if (len(plats) == 0):
        print(f"\n\nYoou don't have secrets")
        return
    else:
        print(f"\n\nYou have {len(plats)}/6 secrets")

    print("Choose the one to eliminate with the identifiers you chose:")
    
    aux=0
    for p in plats:
        print(str(aux+1)+" -> "+p)
        aux=aux+1
    
    r = input("Your selection is: ")
    
    secrets.remove(secrets[int(r)-1])
    plats.remove(plats[int(r)-1])

    return write_file(filename, secrets, plats)
    




def get_board_model(port):
    try:
        result = subprocess.run("sudo udevadm info -q property -n" + port,shell=True,capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if line.startswith("ID_MODEL="):
                return line.split("=")[1]
    except subprocess.CalledProcessError as e:
        print("Erro ao correr udevadm:", e)
    return None


def infer_fqbn(model):
    if model is None:
        return None
    model = model.lower()
    if "micro" in model:
        return "arduino:avr:micro"
    elif "leonardo" in model:
        return "arduino:avr:leonardo"
    elif "uno" in model:
        return "arduino:avr:uno"
    else:
        return None

print("******************************")
print("** Welcome to the TOTPino! ***") 
print("******************************")
print()
print("The script needs to recognize the port")
status = 0
while(status == 0):
    print("\n\n1) If arduino is already connected to the computer, please disconnect for now")
    a = input("Is the arduino disconnected?(y/n) ")
    if(a=="y" or a=="Y"):
        status = 1

out = subprocess.run("sudo ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null",shell=True,capture_output=True, text=True)
first_read = out.stdout

status = 0
while(status == 0):
    print("\n\n2) Now please connect the arduino to one USB port")
    a = input("Is the arduino connected?(y/n) ")
    if(a=="y" or a=="Y"):
        status = 1

out = subprocess.run("sudo ls /dev/ttyUSB* /dev/ttyACM* ",shell=True,capture_output=True, text=True)
second_read = out.stdout

####################
###  Detect Port ###
####################

# Use SequenceMatcher to compare the two
matcher = difflib.SequenceMatcher(None, first_read, second_read)

# Get only the parts that were added in inputB
diff = ''.join(
    second_read[j1:j2]
    for tag, i1, i2, j1, j2 in matcher.get_opcodes()
    if tag == 'insert'
)
port = diff.replace('\n', '')

###################
### Detect FQBN ###
################### 
subprocess.run("sudo apt install udev",shell=True)
model = get_board_model(port)
if (model==None):
    print("Something went wrong. Try to insert model manually:")
    model = input()
fqbn = infer_fqbn(model)
if (fqbn == None):
    print("Something went wrong. Try to insert fqbn manually (ex. arduino:avr:micro):")

print("\n\nThe detected port and fqbn is:")
print(f"PORT={port}")
print(f"FQBN={fqbn}")
a = input("Is this correct? (y/n) ")
if(a == "n" or a == "N"):
    port = input("Insert correct PORT: ")
    fqbn = input("Insert correct FQBN: ")


#subprocess.run(["arduino-cli", "compile", "--fqbn", BOARD_TYPE, "MySketch"])
subprocess.run("snap install arduino-cli",shell=True)
subprocess.run("arduino-cli config init --overwrite", shell=True)
subprocess.run("arduino-cli core install arduino:avr",shell=True)
#arduino-cli lib install "YourLibraryName"
subprocess.run("arduino-cli lib install U8g2",shell=True)
subprocess.run("arduino-cli lib install RTClib",shell=True)

#install crypto.h correctly
path = os.path.expanduser("~/Arduino/libraries/CryptoLegacy")
if not os.path.exists(path):
    subprocess.run("sudo apt install git",shell=True)
    subprocess.run("git clone https://github.com/rweather/arduinolibs.git",shell=True)
    subprocess.run("mv arduinolibs/libraries/CryptoLegacy ~/Arduino/libraries/.",shell=True)
    subprocess.run("mv arduinolibs/libraries/Crypto ~/Arduino/libraries/.",shell=True)
    subprocess.run("rm -rf arduinolibs",shell=True)



filename_secret = "secrets.txt"
status = 0
while(status == 0):
    print("****** Configuration Concluded ******\n\n")
    print("Select one option from the menu:")
    print("1- Insert a secret")
    print("2- Remove a secret")
    print("3- Compile and upload")
    b = int(input("\nYour selection (1-3): "))
    if(b==3):
        status=1
    if(b==1):
        insert_secret(filename_secret)
    if(b==2):
        remove_secret(filename_secret)

#String secret[] = {"vuur2fim7ri3f7ku5xid4754lsz3qeir","NAN","NAN","NAN","NAN","NAN"};
#String plat[] = {"SecretDB","NAN","NAN","NAN","NAN","NAN"};

file_path = 'placeholder.ino'
with open(file_path,'r') as file:
    lines_update = file.readlines()

for i,line in enumerate(lines_update):
    if '/*UPDATE' in line:
        lines_update[i] = ""
    
    if 'UPDATE*/' in line:
        lines_update[i] = ""


with open("update_time/update_time.ino",'w') as file:
    for line in lines_update:
        file.write(line)

# Read the file into a list of lines
##ADD SECRETS
with open(file_path, 'r') as file:
    lines = file.readlines()

secrets, plats = read_file(filename_secret)

missing = 6-len(plats)
if(missing != 0):
    for _ in range(missing):
        plats.append("NAN")

missing = 6-len(secrets)
if(missing != 0):
    for _ in range(missing):
        secrets.append("NAN")

secret_line = "String secret[] = {\""

for i,s in enumerate(secrets):
    secret_line = secret_line + s
    if(i == (len(secrets)-1)):
        secret_line = secret_line + "\"};\n"
    else:
        secret_line = secret_line + "\",\""
    

# Modify the line you want
for i, line in enumerate(lines):
    if 'String secret[] = {"NAN","NAN","NAN","NAN","NAN","NAN"};' in line:
        lines[i] = secret_line


##ADD platforms 
plats_line = "String plat[] = {\""

for i,p in enumerate(plats):
    plats_line = plats_line + p
    if(i == (len(plats)-1)):
        plats_line = plats_line + "\"};\n"
    else:
        plats_line = plats_line + "\",\""

#modify the line 
for i, line in enumerate(lines):
    if 'String plat[] = {"NAN","NAN","NAN","NAN","NAN","NAN"};' in line:
        lines[i] = plats_line

with open("update_secret/update_secret.ino",'w') as file:
    for line in lines:
        file.write(line)

subprocess.run("chmod 777 update_time/update_time.ino",shell=True)
subprocess.run("chmod 777 update_secret/update_secret.ino",shell=True)

def compile_and_upload(fqbn, port, sketch_path):
    print("Compiling...")
    result = subprocess.run("arduino-cli compile --fqbn "+fqbn+" "+sketch_path,shell=True)
    if result.returncode != 0:
        print("ERROR")
        sys.exit(1)

    print("Uploading...")
    result = subprocess.run("arduino-cli upload -p "+port+" --fqbn "+fqbn+" "+sketch_path,shell=True)
    if result.returncode != 0:
        print("ERROR")
        sys.exit(1)

    print("Concluded!")
    

print("Updating time..")
compile_and_upload(fqbn,port,"update_time/update_time.ino")
print("Updating info..")
compile_and_upload(fqbn,port,"update_secret/update_secret.ino")

subprocess.run("rm -rf update_time/update_time.ino",shell=True)
subprocess.run("rm -rf update_secret/update_secret.ino",shell=True)


