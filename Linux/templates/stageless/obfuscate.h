#pragma once
#include <windows.h>
#include <math.h>

static void high_cpu_wait(DWORD milliseconds) {
    LARGE_INTEGER start, freq, current;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&start);
    volatile double dummy = 0.0;
    while (1) {
        QueryPerformanceCounter(&current);
        if ((current.QuadPart - start.QuadPart) * 1000 / freq.QuadPart >= milliseconds)
            break;
        for (int i = 0; i < 1000; i++) {
            dummy += sin(i) * cos(i);
        }
    }
}

static void xor_string(char *dest, const unsigned char *src, size_t len, unsigned char key) {
    for (size_t i = 0; i < len; i++) {
        dest[i] = src[i] ^ key;
    }
    dest[len] = 0;
}
