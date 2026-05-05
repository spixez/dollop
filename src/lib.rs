use pyo3::prelude::*;
use axum::Router;
use std::net::{SocketAddr, ToSocketAddrs};
use evalexpr::*;
use tokio::signal;
use tower_http::services::ServeDir;
use std::fs::File;
use std::io::{BufRead, BufReader};
use sysinfo::{System, Disks, Networks};
use sha2::{Sha256, Digest};
use rand::{thread_rng, Rng};
use rand::distributions::Alphanumeric;
use std::time::Duration;
use tokio::net::TcpStream;
use futures::stream::{self, StreamExt};
use std::collections::HashMap;

fn to_float(v: &Value) -> f64 {
    match v {
        Value::Float(f) => *f,
        Value::Int(i) => *i as f64,
        _ => 0.0,
    }
}

#[pyfunction]
fn evaluate_math(expression: &str) -> PyResult<f64> {
    let mut context = HashMapContext::new();
    let _ = context.set_function("sqrt".into(), Function::new(|v| Ok(Value::Float(to_float(v).sqrt()))));
    let _ = context.set_function("abs".into(), Function::new(|v| Ok(Value::Float(to_float(v).abs()))));
    let _ = context.set_function("sin".into(), Function::new(|v| Ok(Value::Float(to_float(v).sin()))));
    let _ = context.set_function("cos".into(), Function::new(|v| Ok(Value::Float(to_float(v).cos()))));
    let _ = context.set_function("tan".into(), Function::new(|v| Ok(Value::Float(to_float(v).tan()))));
    let _ = context.set_function("log".into(), Function::new(|v| Ok(Value::Float(to_float(v).ln()))));

    match eval_with_context(expression, &context) {
        Ok(value) => {
            if let Value::Float(f) = value { Ok(f) }
            else if let Value::Int(i) = value { Ok(i as f64) }
            else { Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Result not a number")) }
        },
        Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Math error: {}", e))),
    }
}

#[pyfunction]
fn sys_info_data() -> HashMap<String, String> {
    let mut sys = System::new_all();
    sys.refresh_all();
    let mut data = HashMap::new();
    
    data.insert("OS".into(), System::name().unwrap_or_else(|| "Unknown".into()));
    data.insert("Kernel".into(), System::kernel_version().unwrap_or_else(|| "Unknown".into()));
    data.insert("Hostname".into(), System::host_name().unwrap_or_else(|| "Unknown".into()));
    
    if let Some(cpu) = sys.cpus().first() {
        data.insert("CPU_Brand".into(), cpu.brand().to_string());
    }
    data.insert("CPU_Count".into(), sys.cpus().len().to_string());
    data.insert("CPU_Usage".into(), format!("{:.1}", sys.global_cpu_usage()));
    
    data.insert("RAM_Used".into(), (sys.used_memory() / 1024 / 1024).to_string());
    data.insert("RAM_Total".into(), (sys.total_memory() / 1024 / 1024).to_string());
    data.insert("Uptime".into(), System::uptime().to_string());

    // Disks
    let disks = Disks::new_with_refreshed_list();
    let mut disk_info = Vec::new();
    for disk in &disks {
        disk_info.push(format!("{}: {}/{} GB", 
            disk.mount_point().to_string_lossy(),
            disk.available_space() / 1024 / 1024 / 1024,
            disk.total_space() / 1024 / 1024 / 1024
        ));
    }
    data.insert("Disks".into(), disk_info.join(" | "));

    // Networks
    let networks = Networks::new_with_refreshed_list();
    let mut net_info = Vec::new();
    for (interface_name, network) in &networks {
        net_info.push(format!("{}: Rx {}/Tx {} KB", 
            interface_name,
            network.received() / 1024,
            network.transmitted() / 1024
        ));
    }
    data.insert("Networks".into(), net_info.join(" | "));

    data
}

#[pyfunction]
fn compute_dot(v1: Vec<f64>, v2: Vec<f64>) -> PyResult<f64> {
    if v1.len() != v2.len() { return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Vector lengths must match")); }
    let result: f64 = v1.iter().zip(v2.iter()).map(|(a, b)| a * b).sum();
    Ok(result)
}

#[pyfunction]
fn compute_mean(v: Vec<f64>) -> PyResult<f64> {
    if v.is_empty() { return Ok(0.0); }
    let sum: f64 = v.iter().sum();
    Ok(sum / v.len() as f64)
}

#[pyfunction]
fn compute_median(mut v: Vec<f64>) -> PyResult<f64> {
    if v.is_empty() { return Ok(0.0); }
    v.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let mid = v.len() / 2;
    if v.len() % 2 == 0 { Ok((v[mid - 1] + v[mid]) / 2.0) } else { Ok(v[mid]) }
}

#[pyfunction]
fn compute_std_dev(v: Vec<f64>) -> PyResult<f64> {
    if v.is_empty() { return Ok(0.0); }
    let mean = compute_mean(v.clone())?;
    let variance: f64 = v.iter().map(|&x| (x - mean).powi(2)).sum::<f64>() / v.len() as f64;
    Ok(variance.sqrt())
}

#[pyfunction]
fn compute_sort(mut v: Vec<f64>) -> PyResult<Vec<f64>> {
    v.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    Ok(v)
}

#[pyfunction]
fn compute_matrix_mul(a: Vec<Vec<f64>>, b: Vec<Vec<f64>>) -> PyResult<Vec<Vec<f64>>> {
    let rows_a = a.len();
    if rows_a == 0 { return Ok(vec![]); }
    let cols_a = a[0].len();
    let rows_b = b.len();
    if rows_b == 0 { return Ok(vec![]); }
    let cols_b = b[0].len();
    
    for row in &a { if row.len() != cols_a { return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Matrix A is ragged")); } }
    for row in &b { if row.len() != cols_b { return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Matrix B is ragged")); } }

    if cols_a != rows_b { return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Incompatible dimensions")); }
    
    let mut result = vec![vec![0.0; cols_b]; rows_a];
    for i in 0..rows_a {
        for j in 0..cols_b {
            let mut sum = 0.0;
            for k in 0..cols_a { sum += a[i][k] * b[k][j]; }
            result[i][j] = sum;
        }
    }
    Ok(result)
}

#[pyfunction]
fn math_fibonacci(n: u32) -> u64 {
    if n == 0 { return 0; }
    if n == 1 { return 1; }
    let mut a = 0;
    let mut b = 1;
    for _ in 2..=n {
        let temp = a + b;
        a = b;
        b = temp;
    }
    b
}

#[pyfunction]
fn math_factorial(n: u32) -> PyResult<u64> {
    let mut res: u64 = 1;
    for i in 1..=n {
        res = res.checked_mul(i as u64).ok_or_else(|| PyErr::new::<pyo3::exceptions::PyOverflowError, _>("Factorial overflow"))?;
    }
    Ok(res)
}

#[pyfunction]
fn math_is_prime(n: u32) -> bool {
    if n <= 1 { return false; }
    for i in 2..=((n as f64).sqrt() as u32) {
        if n % i == 0 { return false; }
    }
    true
}

#[pyfunction]
fn algo_binary_search(arr: Vec<f64>, target: f64) -> isize {
    let mut low = 0;
    let mut high = arr.len() as isize - 1;
    while low <= high {
        let mid = low + (high - low) / 2;
        if arr[mid as usize] == target { return mid; }
        if arr[mid as usize] < target { low = mid + 1; }
        else { high = mid - 1; }
    }
    -1
}

#[pyfunction]
fn secure_hash(text: &str) -> PyResult<String> {
    let mut hasher = Sha256::new();
    hasher.update(text);
    let result = hasher.finalize();
    Ok(hex::encode(result))
}

#[pyfunction]
fn secure_gen_password(length: usize) -> PyResult<String> {
    let s: String = thread_rng().sample_iter(&Alphanumeric).take(length).map(char::from).collect();
    Ok(s)
}

#[pyfunction]
fn net_my_ip() -> PyResult<String> {
    use local_ip_address::local_ip;
    match local_ip() {
        Ok(ip) => Ok(ip.to_string()),
        Err(e) => Err(PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to get IP: {}", e))),
    }
}

#[pyfunction]
fn net_scan_ports(py: Python<'_>, host: String, start_port: u16, end_port: u16) -> PyResult<Vec<u16>> {
    let rt = tokio::runtime::Runtime::new()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Runtime error: {}", e)))?;
    
    rt.block_on(async {
        let addr_str = format!("{}:{}", host, start_port);
        let resolved_addr = match addr_str.to_socket_addrs() {
            Ok(mut addrs) => addrs.next().ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>("Could not resolve host"))?,
            Err(e) => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid host: {}", e))),
        };
        let ip = resolved_addr.ip();

        let ports = start_port..=end_port;
        let mut results = Vec::new();
        
        let chunks = ports.collect::<Vec<_>>();
        let mut stream = stream::iter(chunks)
            .map(|port| async move {
                let addr = SocketAddr::new(ip, port);
                let conn = tokio::time::timeout(Duration::from_millis(120), TcpStream::connect(&addr)).await;
                match conn {
                    Ok(Ok(_)) => Some(port),
                    _ => None,
                }
            })
            .buffer_unordered(512); 

        while let Some(res) = stream.next().await {
            if let Some(p) = res { results.push(p); }
            if let Err(_) = py.check_signals() {
                return Err(PyErr::new::<pyo3::exceptions::PyKeyboardInterrupt, _>("Cancelled"));
            }
        }
        Ok(results)
    })
}

#[pyfunction]
fn find_in_file(pattern: &str, path: &str) -> PyResult<Vec<String>> {
    let file = File::open(path).map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    let reader = BufReader::new(file);
    let mut results = Vec::new();
    for (idx, line) in reader.lines().enumerate() {
        let l = line.map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        if l.contains(pattern) {
            results.push(format!("{}:{} | {}", path, idx + 1, l));
        }
    }
    Ok(results)
}

#[pyfunction]
fn view_file(path: &str) -> PyResult<Vec<String>> {
    let file = File::open(path).map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to open: {}", e)))?;
    let reader = BufReader::new(file);
    let mut lines = Vec::new();
    for (idx, line) in reader.lines().enumerate() {
        let l = line.map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to read: {}", e)))?;
        lines.push(format!("{:>4} | {}", idx + 1, l));
    }
    Ok(lines)
}

#[pyfunction]
#[pyo3(signature = (port, directory=None))]
fn run_web(port: u16, directory: Option<String>) -> PyResult<()> {
    let dir = directory.unwrap_or_else(|| ".".to_string());
    let rt = tokio::runtime::Runtime::new()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Runtime error: {}", e)))?;
    rt.block_on(async {
        let app = Router::new().fallback_service(ServeDir::new(&dir));
        let addr = SocketAddr::from(([127, 0, 0, 1], port));
        let listener = tokio::net::TcpListener::bind(addr).await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to bind to port {}: {}", port, e)))?;
        axum::serve(listener, app)
            .with_graceful_shutdown(async { signal::ctrl_c().await.ok(); })
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Server error: {}", e)))?;
        Ok(())
    })
}

#[pyfunction]
fn convert_measure(value: f64, from_unit: &str, to_unit: &str) -> PyResult<f64> {
    let result = match (from_unit.to_lowercase().as_str(), to_unit.to_lowercase().as_str()) {
        ("m", "ft") => value * 3.28084, ("ft", "m") => value / 3.28084,
        ("m", "km") => value / 1000.0, ("km", "m") => value * 1000.0,
        ("m", "mi") => value * 0.000621371, ("mi", "m") => value / 0.000621371,
        ("km", "mi") => value * 0.621371, ("mi", "km") => value / 0.621371,
        ("kg", "lb") => value * 2.20462, ("lb", "kg") => value / 2.20462,
        ("c", "f") => (value * 9.0/5.0) + 32.0, ("f", "c") => (value - 32.0) * 5.0/9.0,
        _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Unsupported conversion")),
    };
    Ok(result)
}

#[pymodule]
fn _vron(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(evaluate_math, m)?)?;
    m.add_function(wrap_pyfunction!(convert_measure, m)?)?;
    m.add_function(wrap_pyfunction!(run_web, m)?)?;
    m.add_function(wrap_pyfunction!(sys_info_data, m)?)?;
    m.add_function(wrap_pyfunction!(view_file, m)?)?;
    m.add_function(wrap_pyfunction!(find_in_file, m)?)?;
    m.add_function(wrap_pyfunction!(compute_dot, m)?)?;
    m.add_function(wrap_pyfunction!(compute_mean, m)?)?;
    m.add_function(wrap_pyfunction!(compute_median, m)?)?;
    m.add_function(wrap_pyfunction!(compute_std_dev, m)?)?;
    m.add_function(wrap_pyfunction!(compute_sort, m)?)?;
    m.add_function(wrap_pyfunction!(compute_matrix_mul, m)?)?;
    m.add_function(wrap_pyfunction!(math_fibonacci, m)?)?;
    m.add_function(wrap_pyfunction!(math_factorial, m)?)?;
    m.add_function(wrap_pyfunction!(math_is_prime, m)?)?;
    m.add_function(wrap_pyfunction!(algo_binary_search, m)?)?;
    m.add_function(wrap_pyfunction!(secure_hash, m)?)?;
    m.add_function(wrap_pyfunction!(secure_gen_password, m)?)?;
    m.add_function(wrap_pyfunction!(net_my_ip, m)?)?;
    m.add_function(wrap_pyfunction!(net_scan_ports, m)?)?;
    Ok(())
}
