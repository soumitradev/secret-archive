import gnupg
import warnings
import gzip
import lzma
import json
import os
import re
import shutil
from pathlib import Path
import tarfile

GNUPG_HOME = "./keys/"
VAULT_DIR = "./vault/"
IMPORT_DIR = "./import/"
OUT_PATH = "./out/"

Path(GNUPG_HOME).mkdir(exist_ok=True)
Path(VAULT_DIR).mkdir(exist_ok=True)
Path(IMPORT_DIR).mkdir(exist_ok=True)
Path(OUT_PATH).mkdir(exist_ok=True)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def compress(filename, saveasname, method="gzip"):
    datapath = Path("./import/" + filename)
    vaultpath = Path("./vault/")
    if datapath.exists():
        if method == "gzip":
            with open(datapath, 'rb') as f_in:
                with gzip.open(vaultpath / (saveasname + ".gz"), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        elif method == "lzma":
            with open(datapath, 'rb') as f_in:
                with lzma.open(vaultpath / (saveasname + ".xz"), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            raise ValueError("Unknown compression method specified")
    else:
        raise IOError(
            "No such file! Please enter a valid filename, or ensure the file is in the 'import' folder")


def encrypt(filename, saveasname):
    vaultpath = Path(VAULT_DIR)
    datapath = vaultpath / filename
    if datapath.exists():
        gpg = gnupg.GPG(gnupghome=GNUPG_HOME)
        gpg.encoding = "utf-8"

        key = gpg.gen_key(gpg.gen_key_input())
        fp = key.fingerprint

        with open(datapath, 'rb') as comp_in:
            encrypted_ascii_data = gpg.encrypt_file(
                comp_in, fp, output=vaultpath / saveasname)

    else:
        raise IOError(
            "No such file! Please enter a valid filename, or ensure the file is in the 'vault' folder")


def decrypt(filename, ext, method="gzip"):
    gpg = gnupg.GPG(gnupghome=GNUPG_HOME)
    gpg.encoding = "utf-8"
    vaultpath = Path("./vault/")
    datapath = vaultpath / filename
    if datapath.exists():
        with open(datapath, 'rb') as dec:
            decrypted_data = gpg.decrypt_file(
                dec, output="./vault/" + datapath.name + (("." + ext) if ext else "") + (".gz" if method == "gzip" else ".xz"))
        if not Path("./vault/" + datapath.name + (("." + ext) if ext else "") + (".gz" if method == "gzip" else ".xz")).exists():
            raise Exception("Authentication Failure: No key found for file.")
    else:
        raise IOError(
            "No such file! Please enter a valid filename, or ensure the file is in the 'vault' folder")


def decompress(filename, method="gzip", is_dir=False):
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
        if method == "gzip":
            with gzip.open(datapath, "rb") as f:
                with open(output_dir / (fin_name + (".tar" if is_dir else "")), "wb") as fp:
                    shutil.copyfileobj(f, fp)
        elif method == "lzma":
            with lzma.open(datapath, "rb") as f:
                with open(output_dir / (fin_name + (".tar" if is_dir else "")), "wb") as fp:
                    shutil.copyfileobj(f, fp)
        else:
            raise ValueError("Unknown compression method specified")
    else:
        raise IOError(
            "No such file! Please enter a valid filename, or ensure the file is in the 'vault' folder")


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
            print("Another encrypted file with the same name already exists. " + (("It has the extension ." +
                                                                                   registry[name]['ext']) if registry[name]['ext'] else "It has no extension.") + " Do you want to:\n    [1] - Replace the existing encrypted file\n    [2] - Save the new encrypted file as " + newname)
            k = input(":")
#             Validate input
            while not (k in ["1", "2"]):
                print("\nPlease enter valid input.\nAnother encrypted file with the same name already exists. " + (("It has the extension ." +
                                                                                                                    registry[name]['ext']) if registry[name]['ext'] else "It has no extension.") + " Do you want to:\n    [1] - Replace the existing encrypted file\n    [2] - Save the new encrypted file as " + newname)
                k = input(":")
#             Return name/newname as per input
            if k == "1":
                return name
            else:
                return newname
#     If registry file doesn't exist, return the original name the user intended
    else:
        return name


# Our registry will be in the form of a dictionary. final name is key, and original extension is value.
def addtoreg(final, originalext, method="gz", is_dir=False):
    registry = {}
    regpath = Path("./registry.json")

#     If registry file exists,
    if regpath.exists():
        #         Load the registry into the variable
        with open(regpath, "rb") as regfile:
            registry = json.load(regfile)

        with open(regpath, "w") as regfile:
            registry[final] = {"ext": originalext,
                               "method": method, "is_dir": is_dir}
            json.dump(registry, regfile)
#         If such an encrypted file exists, ask if user wants to rename it.
#     If registry file doesn't exist, add the file to registry and write it to a new registry file.
    else:
        with open(regpath, "w") as regfile:
            registry[final] = {"ext": originalext,
                               "method": method, "is_dir": is_dir}
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
                print(bcolors.WARNING + "Warning: " + bcolors.ENDC +
                      "Unidentified " + ("directory " if i.is_dir() else "file ") + i.name + " in vault")

        todel = [k for k in registry.keys() if k not in [
            m.name for m in list(vaultpath.glob("*"))]]

        for k in todel:
            print(bcolors.WARNING + "Warning: " + bcolors.ENDC + ("Directory " if registry[k]['is_dir'] else "File ") +
                  k + " found in registry, but not in the 'vault' folder.")
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

def writereg(registry):
    regpath = Path("./registry.json")

    with open(regpath, "w") as regfile:
        json.dump(registry, regfile)

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
        imports = list(Path(IMPORT_DIR).glob("*"))
        if not imports:
            raise FileNotFoundError("No files in `import` folder")
        for i, file in enumerate(imports):
            print("[" + str(i) + "]: " + file.name + " : " +
                  ("(folder)" if file.is_dir() else "(file)"))

        name = input(":")
        while not name.isnumeric() or name not in map(str, range(len(imports))):
            print("Please enter a valid choice from the list")
            name = input(":")
        name = int(name)
        is_dir = imports[name].is_dir()
        name = imports[name]
        if "." in name.name:
            stem = ".".join(name.name.split(".")[:-1])
            ext = name.name.split(".")[-1]
        else:
            ext = ""
            stem = name.name

        finalname = getpropername(stem, ext)

        while not (method := input("Compression method [gzip / lzma]: ")) in ["lzma", "gzip"]:
            print("Please enter a valid compression method ('gzip' or 'lzma')")

        if is_dir:
            with tarfile.open(str(name) + ".tar", "w") as tarf:
                tarf.add(name)
            shutil.rmtree(name, ignore_errors=True)
            name = Path(str(name) + ".tar")

        compress(name.name, finalname, method)
        encrypt((finalname + (".gz" if method == "gzip" else ".xz")), finalname)
        os.remove("./vault/" + finalname +
                  (".gz" if method == "gzip" else ".xz"))
        os.remove(name)
        addtoreg(finalname, ext, ("gz" if method == "gzip" else "xz"), is_dir)
        print(("Folder" if is_dir else "File") +
              " encrypted and saved in vault successfully.")
        return
    elif k == "2":
        reg = getreg()
        print("Choose:")

        if not reg:
            raise FileNotFoundError("No files in `import` folder")
        
        names = list(reg.keys())
        exts = [k['ext'] for k in reg.values()]
        methods = [k['method'] for k in reg.values()]
        are_dirs = [k['is_dir'] for k in reg.values()]
        for i in range(len(reg.keys())):
            if exts[i]:
                print("[" + str(i) + "]: " + names[i] +
                      " (." + exts[i] + " file)")
            else:
                if are_dirs[i]:
                    print("[" + str(i) + "]: " +
                        names[i] + " (folder)")
                else:
                    print("[" + str(i) + "]: " +
                        names[i] + " (no extension)")
        num = input(":")
        while not num.isnumeric() or num not in map(str, range(len(reg.keys()))):
            print("Please enter a valid choice from the list")
            num = input(":")
        num = int(num)
        decrypt(names[num], exts[num],
                "gzip" if methods[num] == "gz" else "lzma")
        decompress(names[num] + ("." if exts[num] else "") +
                   exts[num] + (".gz" if methods[num] == "gz" else ".xz"), "gzip" if methods[num] == "gz" else "lzma", are_dirs[num])
        os.remove("./vault/" + names[num] + (("." +
                                              exts[num]) if exts[num] else "") + "." + methods[num])

        os.remove("./vault/" + names[num])
        if are_dirs[num]:
            with tarfile.open(Path(OUT_PATH) / (str(names[num]) + ".tar")) as tarf:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tarf, Path(OUT_PATH))
            shutil.copytree(str(Path(OUT_PATH)/"import"/ names[num]), str(Path(OUT_PATH)/names[num]))
            shutil.rmtree(Path(OUT_PATH)/"import", ignore_errors=True)
            os.remove(Path(OUT_PATH) / (str(names[num]) + ".tar"))
        
        # Remove file from registry
        reg.pop(names[num])

        regpath = Path("./registry.json")

        with open(regpath, "w") as regfile:
            json.dump(reg, regfile)

        updatereg()
        print(("Folder" if are_dirs[num] else "File") +
              " decrypted and saved in `out` folder successfully.")
        return
    else:
        print(bcolors.WARNING + "Warning: " + bcolors.ENDC +
              "Force running files on existing files can potentially result in data loss if files with the same name already exist.\nPlease make sure that you have a backup your data.")
        print("Which function do you want to force run?")
        print(
            "[1] - Compress file\n[2] - Encrypt file\n[3] - Decrypt file\n[4] - Decompress file")
        choice = input(":")

        while not (choice in ["1", "2", "3", "4"]):
            print("Please enter a valid command!")
            print(
                "[1] - Compress file\n[2] - Encrypt file\n[3] - Decrypt file\n[4] - Decompress file")
            choice = input(":")

        if choice == "1":
            print("Choose a file to compress from the `import` folder:")
            imports = list(Path(IMPORT_DIR).glob("*"))
            if not imports:
                raise FileNotFoundError("No files in `import` folder")
            for i, file in enumerate(imports):
                print("[" + str(i) + "]: " + file.name + " : " +
                      ("(folder)" if file.is_dir() else "(file)"))

            name = input(":")
            while not name.isnumeric() or name not in map(str, range(len(imports))):
                print("Please enter a valid choice from the list")
                name = input(":")
            name = int(name)
            is_dir = imports[name].is_dir()
            name = imports[name]
            while not (method := input("Compression method [gzip / lzma]: ")) in ["lzma", "gzip"]:
                print("Please enter a valid compression method ('gzip' or 'lzma')")

            if is_dir:
                print(bcolors.WARNING + "Warning: " + bcolors.ENDC +
                      "compressing folders converts the folder to a tarfile. Decompressing this encrypted file will yield a tarfile that needs to be manually untar-ed.")
                with tarfile.open(str(name) + ".tar", "w") as tarf:
                    tarf.add(name)
                shutil.rmtree(name, ignore_errors=True)
                compress(name.name + ".tar", name.name + ".tar", method)
                os.remove(str(name) + ".tar")
                print("The compressed folder is saved in the `vault` folder.")
                return
            # Make tarfile if is_dir

            compress(name.name, name.name, method)
            print("The compressed file is saved in the `vault` folder.")
        elif choice == "2":
            print("Choose a file to encrypt from the `vault` folder:")
            imports = list(Path(VAULT_DIR).glob("*"))
            
            if not imports:
                raise FileNotFoundError("No files in `vault` folder")
            for i, file in enumerate(imports):
                print("[" + str(i) + "]: " + file.name + " : " +
                      ("(folder)" if file.is_dir() else "(file)"))

            name = input(":")
            while not name.isnumeric() or name not in map(str, range(len(imports))):
                print("Please enter a valid choice from the list")
                name = input(":")
            name = int(name)
            name = imports[name]
            is_dir = name.is_dir()

            if is_dir:
                print(bcolors.WARNING + "Warning: " + bcolors.ENDC +
                      "encrypting folders converts the folder to a tarfile. Decrypting this encrypted file will yield a tarfile that needs to be manually untar-ed.")
                with tarfile.open(str(name) + ".tar", "w") as tarf:
                    tarf.add(name)
                shutil.rmtree(name, ignore_errors=True)
                encrypt(name.name + ".tar", name.name)
                os.remove(str(name) + ".tar")
                print("The encrypted folder is saved in the `vault` folder.")
                return
            encrypt(name.name, name.stem)
            print("The encrypted file is saved in the `vault` folder.")
            return
        elif choice == "3":
            print("Choose a file to decrypt from the `vault` folder:")
            imports = list(Path(VAULT_DIR).glob("*"))
            if not imports:
                raise FileNotFoundError("No files in `vault` folder")
            for i, file in enumerate(imports):
                print("[" + str(i) + "]: " + file.name + " : " +
                      ("(folder)" if file.is_dir() else "(file)"))

            name = input(":")
            while not name.isnumeric() or name not in map(str, range(len(imports))):
                print("Please enter a valid choice from the list")
                name = input(":")
            name = int(name)
            name = imports[name].name
            ext = input(
                "Enter the extension of the file after decrypting (without the `.`): ")
            finalname = getpropername(name, ext)
            decrypt(finalname, ext)
            if ext:
                os.rename("./vault/" + finalname + "." +
                          ext + ".gz", "./vault/" + finalname + "." + ext)
            else:
                os.rename("./vault/" + finalname +
                          ".gz", "./vault/" + finalname)
            print("The decrypted file is saved in the `vault` folder.")
        elif choice == "4":
            print("Choose a file to decompress from the `vault` folder:")
            imports = list(Path(VAULT_DIR).glob("*"))
            if not imports:
                raise FileNotFoundError("No files in `vault` folder")
            for i, file in enumerate(imports):
                print("[" + str(i) + "]: " + file.name + " : " +
                      ("(folder)" if file.is_dir() else "(file)"))

            name = input(":")
            while not name.isnumeric() or name not in map(str, range(len(imports))):
                print("Please enter a valid choice from the list")
                name = input(":")
            name = int(name)
            name = imports[name].name

            while not (method := input("Compression method [gzip / lzma]: ")) in ["lzma", "gzip"]:
                print("Please enter a valid compression method ('gzip' or 'lzma')")
            decompress(name, method)
            print("The decompressed file is saved in the `out` folder.")
        else:
            print("Invalid choice. Quitting.")


init()
