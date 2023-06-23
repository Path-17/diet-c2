pub mod obfwin {
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
