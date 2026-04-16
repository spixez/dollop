# Dollop

High-performance CLI utility suite for computing, network security, and data integrity. Built with a Rust core and Python interface for maximum execution speed and ease of use.

## Features

- **Compute**: Parallel matrix multiplication and statistical analysis (mean, median, standard deviation).
- **Security**: SHA-256 data hashing and cryptographic password generation.
- **Network**: Multi-threaded port scanning and network identity tools.
- **File Utilities**: High-speed text search and buffered file viewing with line numbering.
- **Web**: Concurrent static file server.
- **Interface**: Integrated terminal user interface (TUI) for interactive use.

## Installation

```bash
pip install dollop
```

## Usage

### Interactive Menu
Run the utility without arguments to access the interactive menu:
```bash
dollop
```

### Compute
Perform parallel statistical analysis or matrix operations:
```bash
dollop compute stats "[10, 20, 30, 40, 50]"
dollop compute matmul "[[1, 2], [3, 4]]" "[[5, 6], [7, 8]]"
```

### Network Security
Scan for open ports or retrieve network identity:
```bash
dollop net scan google.com
dollop net ip
```

### Information Assurance
Verify data integrity or generate secure credentials:
```bash
dollop secure hash "data_to_verify"
dollop secure pass 32
```

### File Tools
View large files or search for patterns:
```bash
dollop view logs.txt
dollop find "ERROR" logs.txt
```

### Static Web Server
Serve the current directory over HTTP:
```bash
dollop web 8080 .
```
