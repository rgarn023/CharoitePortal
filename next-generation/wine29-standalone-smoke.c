#define WIN32_LEAN_AND_MEAN
#include <windows.h>

void smoke_entry(void)
{
    static const char message[] = "CHAROITE_WINDOWS_ARM64_SMOKE_OK\r\n";
    DWORD written = 0;
    HANDLE output = GetStdHandle(STD_OUTPUT_HANDLE);

    if (!output || output == INVALID_HANDLE_VALUE ||
        !WriteFile(output, message, sizeof(message) - 1, &written, NULL) ||
        written != sizeof(message) - 1)
        ExitProcess(43);

    ExitProcess(42);
}
