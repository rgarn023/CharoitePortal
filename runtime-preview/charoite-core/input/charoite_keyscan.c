/*
 * Charoite Core / Touhou 8 legacy keyboard bridge.
 *
 * One loopback datagram is one deliberate press/release. The "scan" route
 * sends an actual scan code through Wine SendInput after attempting to
 * activate the game window. The alternative "window" route sends WM_KEY*
 * directly to the game's HWND. This is a fallback, not injected game code.
 *
 * Fixed-size packets: CKS1 or CKW1, VK, pressed (0 or 1).
 * ACK: CKA1 followed by '1' SendInput accepted, '2' WM_KEY event posted,
 * 'N' target window unavailable, or '0' delivery failure.
 */
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <windows.h>
#include <tlhelp32.h>
#include <wchar.h>
#include <stdint.h>
#pragma comment(lib, "ws2_32.lib")

typedef struct {
    HWND hwnd;
    unsigned long size;
    DWORD pid;
} GameWindow;

static BOOL recognizedGame(DWORD pid) {
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) return FALSE;
    PROCESSENTRY32W process;
    ZeroMemory(&process, sizeof(process));
    process.dwSize = sizeof(process);
    BOOL recognized = FALSE;
    if (Process32FirstW(snapshot, &process)) do {
        if (process.th32ProcessID != pid) continue;
        const wchar_t *name = process.szExeFile;
        recognized = (_wcsnicmp(name, L"th08", 4) == 0) ||
                (_wcsnicmp(name, L"imperishable", 12) == 0);
        break;
    } while (Process32NextW(snapshot, &process));
    CloseHandle(snapshot);
    return recognized;
}

static BOOL CALLBACK selectGameWindow(HWND hwnd, LPARAM context) {
    GameWindow *out = (GameWindow*)context;
    DWORD pid = 0;
    GetWindowThreadProcessId(hwnd, &pid);
    if (!pid || !recognizedGame(pid) || !IsWindowVisible(hwnd) ||
            !IsWindowEnabled(hwnd)) return TRUE;
    RECT rect;
    if (!GetWindowRect(hwnd, &rect)) return TRUE;
    int width = rect.right - rect.left;
    int height = rect.bottom - rect.top;
    if (width < 200 || height < 140) return TRUE;
    unsigned long area = (unsigned long)width * (unsigned long)height;
    if (area > out->size) {
        out->hwnd = hwnd;
        out->pid = pid;
        out->size = area;
    }
    return TRUE;
}

static HWND findGameWindow(void) {
    GameWindow choice;
    ZeroMemory(&choice, sizeof(choice));
    EnumWindows(selectGameWindow, (LPARAM)&choice);
    if (!choice.hwnd) EnumChildWindows(GetDesktopWindow(),
            selectGameWindow, (LPARAM)&choice);
    return choice.hwnd;
}

static void focusGame(HWND hwnd) {
    if (!hwnd || !IsWindow(hwnd)) return;
    DWORD targetThread = GetWindowThreadProcessId(hwnd, NULL);
    DWORD ourThread = GetCurrentThreadId();
    BOOL attached = targetThread && targetThread != ourThread &&
            AttachThreadInput(ourThread, targetThread, TRUE);
    BringWindowToTop(hwnd);
    SetForegroundWindow(hwnd);
    if (attached) {
        SetFocus(hwnd);
        AttachThreadInput(ourThread, targetThread, FALSE);
    }
}

static unsigned char sendGameKey(HWND hwnd, unsigned char virtualKey,
                                 int pressed, int postWindowMessage) {
    if (postWindowMessage && !hwnd) return 'N';
    UINT scan = MapVirtualKeyW(virtualKey, MAPVK_VK_TO_VSC_EX);
    if (!scan) return '0';
    UINT scanLow = scan & 0xff;
    if (postWindowMessage) {
        LPARAM keyInfo = 1 | ((LPARAM)scanLow << 16);
        if (scan & 0xff00) keyInfo |= ((LPARAM)1 << 24);
        if (!pressed) keyInfo |= ((LPARAM)3 << 30);
        BOOL ok = PostMessageW(hwnd, pressed ? WM_KEYDOWN : WM_KEYUP,
                               virtualKey, keyInfo);
        return ok ? '2' : '0';
    }
    focusGame(hwnd);
    INPUT input;
    ZeroMemory(&input, sizeof(input));
    input.type = INPUT_KEYBOARD;
    input.ki.wVk = 0;
    input.ki.wScan = (WORD)scanLow;
    input.ki.dwFlags = KEYEVENTF_SCANCODE |
            ((scan & 0xff00) ? KEYEVENTF_EXTENDEDKEY : 0) |
            (!pressed ? KEYEVENTF_KEYUP : 0);
    return SendInput(1, &input, sizeof(input)) == 1 ? '1' : '0';
}

int WINAPI WinMain(HINSTANCE instance, HINSTANCE previous, LPSTR args, int shown) {
    (void)instance; (void)previous; (void)args; (void)shown;
    WSADATA ws;
    if (WSAStartup(MAKEWORD(2, 2), &ws) != 0) return 2;
    SOCKET server = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (server == INVALID_SOCKET) { WSACleanup(); return 3; }
    struct sockaddr_in listen_at;
    ZeroMemory(&listen_at, sizeof(listen_at));
    listen_at.sin_family = AF_INET;
    listen_at.sin_port = htons(7949);
    listen_at.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(server, (const struct sockaddr*)&listen_at,
             sizeof(listen_at)) == SOCKET_ERROR) {
        closesocket(server); WSACleanup(); return 4;
    }
    for (;;) {
        unsigned char payload[16];
        struct sockaddr_in peer;
        int peerSize = sizeof(peer);
        int len = recvfrom(server, (char*)payload, sizeof(payload), 0,
                           (struct sockaddr*)&peer, &peerSize);
        if (len != 6 || payload[0] != 'C' || payload[1] != 'K' ||
                (payload[2] != 'S' && payload[2] != 'W') ||
                payload[3] != '1' ||
                (payload[5] != 0 && payload[5] != 1)) continue;
        HWND hwnd = findGameWindow();
        unsigned char status = sendGameKey(hwnd, payload[4], payload[5],
                                          payload[2] == 'W');
        const char ack[5] = {'C','K','A','1',(char)status};
        sendto(server, ack, sizeof(ack), 0, (struct sockaddr*)&peer, peerSize);
    }
    return 0;
}
