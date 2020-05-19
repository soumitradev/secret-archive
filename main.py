import gnupg
import gzip
import json
import re
import shutil

from pathlib import Path
import os

def compress(filename):
    datapath = Path("./import/"  + filename)
    vaultpath = Path("./vault/")
    if datapath.exists():
        with open(datapath, 'rb') as f_in:
            with gzip.open(vaultpath / (datapath.stem + ".gz"), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    else:
        raise IOError("No such file! Please enter a valid filename, or ensure the file is in the 'import' folder")

def encrypt(filename):
    vaultpath = Path("./vault/")
    datapath = vaultpath / Path(filename)
    if datapath.exists():
        gpg = gnupg.GPG()
        gpg.encoding = "utf-8"


        key = gpg.gen_key(gpg.gen_key_input())
        fp = key.fingerprint

        with open(datapath, 'rb') as comp_in:
            encrypted_ascii_data = gpg.encrypt_file(comp_in, fp, output = vaultpath / datapath.stem)
    
    else:
        raise IOError("No such file! Please enter a valid filename, or ensure the file is in the 'vault' folder")
        
def decrypt(filename, ext):
    gpg = gnupg.GPG()
    gpg.encoding = "utf-8"
    vaultpath = Path("./vault/")
    datapath = vaultpath / Path(filename)
    if datapath.exists():
        with open(datapath, 'rb') as dec:
            decrypted_data = gpg.decrypt_file(dec, output = "./vault/" + datapath.stem + "." + ext + ".gz")
    else:
        raise IOError("No such file! Please enter a valid filename, or ensure the file is in the 'vault' folder")
        
def decompress(filename):
    vaultpath = Path("./vault/")
    datapath = vaultpath / Path(filename)
    outpath = "./"
    original_extension = datapath.stem.split(".")[-1]
    name = datapath.stem.split(".")[0]
    if datapath.exists():
        with gzip.open(datapath, "rb") as f:
            with open(outpath / Path(name + "." + original_extension), "wb") as fp:
                shutil.copyfileobj(f, fp)
    else:
        raise IOError("No such file! Please enter a valid filename, or ensure the file is in the 'vault' folder")

# Our registry will be in the form of a dictionary. final name is key, and original extension is value.
def addtoreg(final, originalext):
    registry = {}
    regpath = Path("./registry.json")
    
#     If registry file exists,
    if regpath.exists():
#         Load the registry into the variable
        with open(regpath, "rb") as regfile:
            registry = json.load(regfile)
#         If such an encrypted file doesn't already exist, add it to registry and write registry to disk
        if not (final in registry):
            with open(regpath, "w") as regfile:
                registry[final] = originalext
                json.dump(registry, regfile)
                
#         If such an encrypted file exists, ask if user wants to rename it.
        else:
#         Nice litte code block that finds the new name for the renamed file
#         If the file name ends in a number enclosed in brackets, increment the number for the new name until such a file doesn't exist
            if re.match(".*\(\d\)", final):
                newname = final
                while (newname in registry):
                    name = final.split("(")[0]
                    number = int(final.split("(")[1][:-1])
                    newname = name + "(" + str(number + 1) + ")"
#         Else, just add a ' (1)' at the end of the file
            else:
                newname = final + " (1)"
            
#             Print error and input prompt
            print("Another encrypted file with the same name already exists. It has the extension ." + registry[final] + " Do you want to:\n    [1] - Replace the existing encrypted file\n    [2] - Save the new encrypted file as " + newname)
            k = input()
        
#             Validate input
            while not (k in ["1", "2"]):
                print("\nPlease enter valid input.\nAnother encrypted file with the same name already exists. It has the extension ." + registry[final] + " Do you want to:\n    [1] - Replace the existing encrypted file\n    [2] - Save the new encrypted file as " + newname)
                k = input()
            
#             Perform action as per input
            if k == "1":
                registry[final] = originalext
            else:
                registry[newname] = originalext
                
#             Write registry to disk
            with open(regpath, "w") as regfile:
                json.dump(registry, regfile)
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
            if not (i.stem in registry):
                raise IOError("Unidentified file " + i.stem + " in vault")
        
        todel = []
        print(list(vaultpath.glob("*")))
        for j in registry.keys():
            paths = list(vaultpath.glob("*"))
            names = []
            for m in paths:
                print(m.stem)
                names.append(m.stem)
            if not(j in names):
                todel.append(j)
        
        for k in todel:
            registry.pop(k, None)

        with open(regpath, "w") as regfile:
            json.dump(registry, regfile)

def getreg():
    updatereg()
    registry = {}
    vaultpath = Path("./vault/")
    regpath = Path("./registry.json")
    
    if regpath.exists():
        with open(regpath, "rb") as regfile:
            registry = json.load(regfile)
    return registry

def init():
    print("1: encrypt, compress and store in vault; 2: decrypt, decompress and give final file\n")
    k = input()
    if k == "1":
        updatereg()
        print("Enter filename with extension: ")
        name = input()
        stem = name.split(".")[0]
        ext = name.split(".")[1]

        compress(name)
        encrypt(stem + ".gz")
        os.remove("./vault/" + stem + ".gz")
        addtoreg(stem, ext)
    else:
        print("Choose:")
        reg = getreg()
        names = list(reg.keys())
        exts = list(reg.values())
        for i in range(len(reg.keys())):
            print("[" + str(i) + "]: " + names[i] + " (." + exts[i] + " file)")
        num = int(input())
        decrypt(names[num], exts[num])
        decompress(names[num] + "." + exts[num] + ".gz")
        os.remove("./vault/" + names[num] + "." + exts[num] + ".gz")
        os.remove("./vault/" + names[num])
        updatereg()

init()

# Known issues:
# When file is added as "file (1)" into the registry, it is still encrypted and saved as "file"
# If file doesn't have extension, what do?
# Error handling and user input validation