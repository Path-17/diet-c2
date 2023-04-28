from typing import List

# This is the file that descibes the functions that handle client commands

# Command that sends a shell command to the implant
def cmd_shell(args: List[str]):
    return
# Command that sends a shellcode file to the server as well as a command
# The command is read first, and tells the implant where to pull the 
# shellcode file from on the server, reads it into memory, and executes
def cmd_shellcode_inject(args: List[str]):
    return
# Different method of shellcode injection, this creates a process and injects it
# into it, same client -> server -> implant transfer method as shellcode_inject
def cmd_shellcode_spawn(args: List[str]):
    return

# Here is the dict of commands 
CMD_TABLE = {
                "shell": cmd_shell,
                "shellcode-inject": cmd_shellcode_inject,
                "shellcode-spawn": cmd_shellcode_spawn,
}

