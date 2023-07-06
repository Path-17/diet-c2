[SECTION .data]
currentHash:    dd  0

[SECTION .text]

BITS 64
DEFAULT REL

global NtAllocateVirtualMemory
global NtWriteVirtualMemory
global NtCreateThreadEx
global NtWaitForSingleObject
global NtClose

global WhisperMain
extern SW2_GetSyscallNumber
    
WhisperMain:
    pop rax
    mov [rsp+ 8], rcx              ; Save registers.
    mov [rsp+16], rdx
    mov [rsp+24], r8
    mov [rsp+32], r9
    sub rsp, 28h
    mov ecx, dword [currentHash]
    call SW2_GetSyscallNumber
    add rsp, 28h
    mov rcx, [rsp+ 8]              ; Restore registers.
    mov rdx, [rsp+16]
    mov r8, [rsp+24]
    mov r9, [rsp+32]
    mov r10, rcx
    syscall                        ; Issue syscall
    ret

NtAllocateVirtualMemory:
    mov dword [currentHash], 0859D60F6h    ; Load function hash into global variable.
    call WhisperMain                       ; Resolve function hash into syscall number and make the call

NtWriteVirtualMemory:
    mov dword [currentHash], 0B135979Bh    ; Load function hash into global variable.
    call WhisperMain                       ; Resolve function hash into syscall number and make the call

NtCreateThreadEx:
    mov dword [currentHash], 050BC86E2h    ; Load function hash into global variable.
    call WhisperMain                       ; Resolve function hash into syscall number and make the call

NtWaitForSingleObject:
    mov dword [currentHash], 078550ABAh    ; Load function hash into global variable.
    call WhisperMain                       ; Resolve function hash into syscall number and make the call

NtClose:
    mov dword [currentHash], 0B6235FADh    ; Load function hash into global variable.
    call WhisperMain                       ; Resolve function hash into syscall number and make the call

