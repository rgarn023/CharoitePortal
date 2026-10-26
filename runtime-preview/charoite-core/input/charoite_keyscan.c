/*
 * Charoite Core scan-code keyboard bridge for older Win32/DirectInput games.
 * Runs inside the selected Wine container. It accepts ONLY a fixed six-byte
 * keyboard request on loopback; no commands, filenames or arbitrary payloads.
 * The Android client receives an acknowledgement indicating SendInput result.
 */
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <windows.h>
#include <stdint.h>
#pragma comment(lib, "ws2_32.lib")

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
    if (bind(server, (const struct sockaddr*)&listen_at, sizeof(listen_at)) == SOCKET_ERROR) {
        closesocket(server); WSACleanup(); return 4;
    }
    for (;;) {
        unsigned char payload[16];
        struct sockaddr_in peer;
        int peerSize = sizeof(peer);
        int len = recvfrom(server, (char*)payload, sizeof(payload), 0,
                           (struct sockaddr*)&peer, &peerSize);
        if (len != 6 || payload[0] != 'C' || payload[1] != 'K' ||
                payload[2] != 'S' || payload[3] != '1' ||
                (payload[5] != 0 && payload[5] != 1)) continue;
        UINT vkey = payload[4];
        UINT scan = MapVirtualKeyW(vkey, MAPVK_VK_TO_VSC_EX);
        unsigned char result = '0';
        if (scan != 0) {
            INPUT input;
            ZeroMemory(&input, sizeof(input));
            input.type = INPUT_KEYBOARD;
            input.ki.wVk = 0; // KEYEVENTF_SCANCODE requires scan code, not VK
            input.ki.wScan = (WORD)(scan & 0xff);
            input.ki.dwFlags = KEYEVENTF_SCANCODE |
                    ((scan & 0xff00) ? KEYEVENTF_EXTENDEDKEY : 0) |
                    (payload[5] == 0 ? KEYEVENTF_KEYUP : 0);
            result = SendInput(1, &input, sizeof(INPUT)) == 1 ? '1' : '0';
        }
        // CKA1 + 1|0 denotes a real Wine-side scan-code injection attempt.
        const char ack[5] = {'C','K','A','1',(char)result};
        sendto(server, ack, sizeof(ack), 0, (struct sockaddr*)&peer, peerSize);
    }
    return 0;
}
