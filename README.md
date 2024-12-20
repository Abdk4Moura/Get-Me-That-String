# File Search Server and Client

This project implements a multithreaded server-client architecture designed to handle secure and efficient string matching in large files. The server processes client queries for exact matches in a text file, with support for SSL encryption and high concurrency.

## Project Goals
- **High Performance:** Handle multiple concurrent client connections efficiently using multithreading.
- **Security:** Support SSL/TLS for encrypted communication between the server and clients.
- **Flexibility:** Provide robust configuration management for both server and client.
- **Test Coverage:** Ensure reliability through comprehensive automated tests.

## Features
### Server
- **String Matching:** Performs exact string matching on a file provided via a configuration file.
- **Multithreading:** Efficiently handles multiple client connections concurrently.
- **SSL Support:** Optional encryption for secure communication.
- **Dynamic File Reading:** Supports both cached and dynamic file reading modes (`REREAD_ON_QUERY`).
- **Logging:** Provides detailed logs for debugging and monitoring.

### Client
- **Query Execution:** Sends queries to the server and retrieves responses.
- **SSL Support:** Optional encryption for secure communication.

## Getting Started

### Prerequisites
- Python 3.8+
- `poetry` (for dependency management)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```
2. Install dependencies:
   ```bash
   poetry install
   ```

### Configuration
#### Server Configuration
The server expects a configuration file (e.g., `config.ini`) with the following format:
```ini
[Server]
port=44445
ssl=True
reread_on_query=True
linuxpath=/path/to/file.txt
certfile=server.crt
keyfile=server.key
```
- **`linuxpath`**: Path to the file used for string matching.
- **`ssl`**: Enable or disable SSL.
- **`reread_on_query`**: Whether to reload the file on every query.

#### Client Configuration
The client configuration is passed via command-line arguments or an optional config file:
```ini
[Client]
server=127.0.0.1
port=44445
query="search_term"
ssl=True
certfile=client.crt
keyfile=client.key
```

### Usage
#### Running the Server
1. Start the server by specifying the configuration file:
   ```bash
   python server.py --config /path/to/config.ini
   ```
2. Monitor logs in the console or `server.log`.

#### Running the Client
1. Send queries to the server:
   ```bash
   python client.py --server <server-ip> --port <port> --query "search_term" [--ssl_enabled] [--cert_file <cert>] [--key_file <key>]
   ```

### Testing
Run the test suite to validate functionality:
```bash
pytest --cov=core tests/
```

## Directory Structure
```
AlgoAssessment/
├── core/                # Core application logic
├── tests/               # Automated test suite
├── config.ini           # Example server configuration
├── test_config.ini      # Test configuration
├── README.md            # Project documentation
├── server.py            # Server script
├── client.py            # Client script
├── logging_setup.py     # Centralized logging module
├── config.py            # Configuration classes
```

## Known Issues
- High memory usage for large files in `REREAD_ON_QUERY=False` mode.

## Future Improvements
- Add rate limiting for client connections.
- Optimize memory usage for dynamic file reading.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for suggestions.

## License
This project is licensed under the MIT License.
