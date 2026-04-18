CC = x86_64-w64-mingw32-clang
CFLAGS = -O0 -Wall -w -fms-extensions -fdeclspec -static -I/usr/x86_64-w64-mingw32/include
LDFLAGS = -L/usr/x86_64-w64-mingw32/lib -Wl,--disable-auto-import -s -mwindows
LIBS = -lwinhttp -lntdll -lm -lshell32
NASM = nasm
NASMFLAGS = -f win64

ALL_C = $(wildcard *.c)
ifeq ($(FORMAT),DLL)
    C_SRCS := $(ALL_C)
    TARGET := afloader.dll
    CFLAGS += -DAF_AS_DLL
    LDFLAGS := -shared $(LDFLAGS)
else
    C_SRCS := $(filter-out main_dll.c, $(ALL_C))
    TARGET := afloader.exe
endif

C_OBJS = $(C_SRCS:.c=.o)
ASM_SRC = whispers-asm.x64.asm
ASM_OBJ = whispers-asm.o

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(C_OBJS) $(ASM_OBJ)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) $(LIBS) -o $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

$(ASM_OBJ): $(ASM_SRC)
	$(NASM) $(NASMFLAGS) $< -o $@

clean:
	rm -f $(C_OBJS) $(ASM_OBJ) $(TARGET)
