# Diet C2
Lightweight C2 using python3 for the server and client, with a C++ implant.

Used as a tool to learn and implement red team techniques at a low level.

## Current Commands

- shellcode-inject - Inject shellcode into a given PID (Both allocating RWX -> write -> execute OR allocating RW -> write -> RX -> execute)
- shellcode-spawn - Run shellcode in a new thread of the current process (Both allocating RWX -> write -> execute OR allocating RW -> write -> RX -> execute)
- shellcode-earlybird - Run shellcode using the earlybird technique (Both allocating RWX -> write -> execute OR allocating RW -> write -> RX -> execute)
- shell - Run a command using cmd.exe without showing the command prompt popup, and get back the output of the command
- kill - Kill the selected implant, and cleanly exit out of the process

**Each command has an -direct or -indirect flag to use direct or indirect syscalls**

## Milestones

- [x] Designing the Architecture - Making a plan for *how* a command will be sent from the C2 to the server to the implant, and how output will be returned
- [x] Foundational Features - Coding up the UI, command processing and overall file structure in such a way that it is easy to add a new command or feature
- **New Commands** (**IN PROGRESS**) - Implementing different commands used by other C2s and anything new I can think of
- [x] AV Avoidance - Using encryption, WinAPI call obfuscation and other methods to avoid getting flagged by AntiVirus solutions
- Documentation - Self explanatory, but very difficult to write good docs, will be done throughout the development
- (**IN PROGRESS**) Obfuscation - Make the implant hard to detect when looking for it, having believable communications with the server for example
- New Server / Implant modules - New type of listener for example, a staged implant payload, or an implant written in powershell and so on
- Operationalize and Polish
