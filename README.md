# Diet C2
Lightweight C2 using python3 for the server and client, with a C++ implant.

Used as a tool to learn and implement red team techniques at a low level.

## TODOS

Client
- [ ] DLL injection command (file upload)

Server
- [ ] Implement a system to save the state when the server is closed, that can be loaded when opened again

Implant
- [ ] Implement DLL injection (command parse -> download -> inject)

## Milestones

1. [x] Designing the Architecture - Making a plan for *how* a command will be sent from the C2 to the server to the implant, and how output will be returned
1. [x] Foundational Features - Coding up the UI, command processing and overall file structure in such a way that it is easy to add a new command or feature
2. [o] New Commands - Implementing different commands used by other C2s and anything new I can think of, 
4. [ ] AV Avoidance - Using encryption, WinAPI call obfuscation and other methods to avoid getting flagged by AntiVirus solutions
5. [ ] Documentation - Self explanatory, but very difficult to write good docs, will be done throughout the development
6. [ ] Obfuscation - Make the implant hard to detect when looking for it, having believable communications with the server for example`
7. [ ] New Server / Implant modules - New type of listener for example, a staged implant payload, or an implant written in powershell and so on
8. [ ] Operationalize and Polish
