import gnupg
import gzip
import json
import os
import re
import shutil
from pathlib import Path

GNUPG_HOME = "./keys/"
VAULT_DIR = "./vault/"
IMPORT_DIR = "./import/"
OUT_PATH = "./out/"

Path(GNUPG_HOME).mkdir(exist_ok=True)
Path(VAULT_DIR).mkdir(exist_ok=True)
Path(IMPORT_DIR).mkdir(exist_ok=True)
Path(OUT_PATH).mkdir(exist_ok=True)

def compress(filename, saveasname):
    datapath = Path("./import/"  + filename)
    vaultpath = Path("./vault/")
    if datapath.exists():
        with open(datapath, 'rb') as f_in:
            with gzip.open(vaultpath / (saveasname + ".gz"), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    else:
        raise IOError("No such file! Please enter a valid filename, or ensure the file is in the 'import' folder")

def encrypt(filename, saveasname):
    vaultpath = Path("./vault/")
    datapath = vaultpath / filename
    if datapath.exists():
        gpg = gnupg.GPG(gnupghome=GNUPG_HOME)
        gpg.encoding = "utf-8"


        key = gpg.gen_key(gpg.gen_key_input())
        fp = key.fingerprint

        with open(datapath, 'rb') as comp_in:
            encrypted_ascii_data = gpg.encrypt_file(comp_in, fp, output = vaultpath / saveasname)
    
    else:
        raise IOError("No such file! Please enter a valid filename, or ensure the file is in the 'vault' folder")
        
def decrypt(filename, ext):
    gpg = gnupg.GPG(gnupghome= GNUPG_HOME)
    gpg.encoding = "utf-8"
    vaultpath = Path("./vault/")
    datapath = vaultpath / filename
    if datapath.exists():
        with open(datapath, 'rb') as dec:
            decrypted_data = gpg.decrypt_file(dec, output = "./vault/" + datapath.name + (("." + ext) if ext else "") + ".gz")
    else:
        raise IOError("No such file! Please enter a valid filename, or ensure the file is in the 'vault' folder")
        
def decompress(filename):
    vaultpath = Path("./vault/")
    datapath = vaultpath / filename
    output_dir = Path(OUT_PATH)
    fin_name = datapath.stem

    # if "." in datapath.stem:
    #     original_extension = "." + datapath.stem.split(".")[-1]
    #     name = datapath.stem.split(".")[0]
    # else:
    #     original_extension = ""
    #     name = datapath.stem

    if datapath.exists():
        with gzip.open(datapath, "rb") as f:
            with open(output_dir / fin_name, "wb") as fp:
                shutil.copyfileobj(f, fp)
    else:
        raise IOError("No such file! Please enter a valid filename, or ensure the file is in the 'vault' folder")

def getpropername(name, extension):
    registry = {}
    regpath = Path("./registry.json")

#     If registry file exists,
    if regpath.exists():
#         Load the registry into the variable
        with open(regpath, "rb") as regfile:
            registry = json.load(regfile)
#         If such an encrypted file doesn't already exist, return the name the user wanted
        if not (name in registry):
            return name
                
#         If such an encrypted file exists, ask if user wants to rename it.
        else:
#         Nice litte code block that finds the new name for the renamed file
#         If the file name ends in a number enclosed in brackets, increment the number for the new name until such a file doesn't exist
            newname = name
            while (newname in registry):
                if re.match(".*\(\d\)", newname):
                    while (newname in registry):
                        initial_part = newname.split("(")[0]
                        number = int(newname.split("(")[1][:-1])
                        newname = initial_part + "(" + str(number + 1) + ")"
    #         Else, just add a ' (1)' at the end of the file
                else:
                    newname += " (1)"
            
#             Print error and input prompt
            print("Another encrypted file with the same name already exists. It has the extension ." + registry[name] + " Do you want to:\n    [1] - Replace the existing encrypted file\n    [2] - Save the new encrypted file as " + newname)
            k = input()
        
#             Validate input
            while not (k in ["1", "2"]):
                print("\nPlease enter valid input.\nAnother encrypted file with the same name already exists. It has the extension ." + registry[name] + " Do you want to:\n    [1] - Replace the existing encrypted file\n    [2] - Save the new encrypted file as " + newname)
                k = input()
            
#             Return name/newname as per input
            if k == "1":
                return name
            else:
                return newname
                
#     If registry file doesn't exist, return the original name the user intended
    else:
        return name



# Our registry will be in the form of a dictionary. final name is key, and original extension is value.
def addtoreg(final, originalext):
    registry = {}
    regpath = Path("./registry.json")

#     If registry file exists,
    if regpath.exists():
#         Load the registry into the variable
        with open(regpath, "rb") as regfile:
            registry = json.load(regfile)

        with open(regpath, "w") as regfile:
            registry[final] = originalext
            json.dump(registry, regfile)
                
#         If such an encrypted file exists, ask if user wants to rename it.
#     If registry file doesn't exist, add the file to registry and write it to a new registry file.
    else:
        with open(regpath, "w") as regfile:
            registry[final] = originalext
            json.dump(registry, regfile)


def updatereg():
    registry = {}
    vaultpath = Path("./vault/")
    regpath = Path("./registry.json")
    
    if regpath.exists():
        with open(regpath, "rb") as regfile:
            registry = json.load(regfile)
            
        for i in list(vaultpath.glob("*")):
            if not (i.name in registry):
                raise IOError("Unidentified file " + i.name + " in vault")
        
        todel = [k for k in registry.keys() if k not in [m.name for m in list(vaultpath.glob("*"))]]
        
        for k in todel:
            print(f"File {k} found in registry, but not in the 'vault' folder.")
            # registry.pop(k, None)

        with open(regpath, "w") as regfile:
            json.dump(registry, regfile)

def getreg():
    updatereg()
    registry = {}
    regpath = Path("./registry.json")
    
    if regpath.exists():
        with open(regpath, "rb") as regfile:
            registry = json.load(regfile)
    return registry

def init():
    print("Welcome to Secret Archive! Please choose an action:")
    print("[1] - Compress, Encrypt and add file to vault\n[2] - Decrypt, Decompress and remove file from vault\n[3] - Force run algorithm on file")
    k = input(":")
    while not (k in ["1", "2", "3"]):
        print("Please enter a valid command!")
        print("[1] - Compress, Encrypt and add file to vault\n[2] - Decrypt, Decompress and remove file from vault\n[3] - Force run algorithm on file")
        k = input(":")

    if k == "1":
        updatereg()
        print("Enter filename with extension: ")
        name = input()
        if "." in name:
            stem = ".".join(name.split(".")[:-1])
            ext = name.split(".")[-1]
        else:
            ext = ""
            stem = name

        finalname = getpropername(stem, ext)
        compress(name, finalname)
        encrypt((finalname + ".gz"), finalname)
        os.remove("./vault/" + finalname + ".gz")
        addtoreg(finalname, ext)
    elif k == "2":
        print("Choose:")
        reg = getreg()
        names = list(reg.keys())
        exts = list(reg.values())
        for i in range(len(reg.keys())):
            if exts[i]:
                print("[" + str(i) + "]: " + names[i] + " (." + exts[i] + " file)")
            else:
                print("[" + str(i) + "]: " + names[i] + " (no extension known)")
        num = int(input())
        decrypt(names[num], exts[num])
        decompress(names[num] + "." + exts[num] + ".gz")
        os.remove("./vault/" + names[num] + ("." + exts[num] if exts[num] else "") + ".gz")

        # os.remove("./vault/" + names[num])
        updatereg()
    else:
        print("Which function do you want to force run?")
        print("[1] - Compress file\n[2] - Encrypt file\n[3] - Decrypt file\n[4] - Decompress file")
        choice = input(":")

        while not (choice in ["1", "2", "3", "4"]):
            print("Please enter a valid command!")
            print("[1] - Compress file\n[2] - Encrypt file\n[3] - Decrypt file\n[4] - Decompress file")
            choice = input(":")
        
        if choice == "1":
            name = input("Move file to the 'import' folder and type the name here: ")
            compress(name, name)
            print("The compressed file is saved in the 'vault' folder.")
        elif choice == "2":
            name = input("Move file to the 'vault' folder and type the name here: ")
            encrypt(name, name)
            print("The encyrypted file is saved in the 'vault' folder.")
        elif choice == "3":
            name = input("Move file to the 'vault' folder and type the name here: ")
            ext = input("Enter the extension of the file after decrypting: ")
            finalname = getpropername(name, ext)
            decrypt(finalname, ext)
            if ext:
                os.rename("./vault/" + finalname + "." + ext + ".gz", finalname + "." + ext)
            else:
                os.rename("./vault/" + finalname + "." + ext + ".gz", finalname)
            print("The decrypted file is saved in the root folder of this program.")
        else:
            name = input("Move file to the 'vault' folder and type the name here: ")
            decompress(name)
            print("The decompressed file is saved in the root folder of this program.")

init()