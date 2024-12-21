# AlgoAssessment: A String Matching Server

This project implements a multithreaded TCP server that efficiently searches for exact string matches within a file. The server is highly configurable and designed to be robust and performant. This document will guide you from setting up the project, to running the tests, and how to use the server and the client applications.

## Table of Contents

- [Project Description](#project-description)
- [Setup and Installation](#setup-and-installation)
    - [Prerequisites](#prerequisites)
    - [Setting Up the Virtual Environment](#setting-up-the-virtual-environment)
    - [Installing Dependencies](#installing-dependencies)
    - [Alternative Method using `requirements.txt`](#alternative-method-using-requirements.txt)
- [Project Structure](#project-structure)
- [Running the Server](#running-the-server)
    - [Required Configuration](#required-configuration)
    - [Optional Server Configuration](#optional-server-configuration)
    - [Using Dynamically Assigned Ports](#using-dynamically-assigned-ports)
    - [Running as a systemd Service](#running-as-a-systemd-service)
    - [Running as a Standalone Daemon](#running-as-a-standalone-daemon)
- [Using the Client](#using-the-client)
    - [Client Usage](#client-usage)
- [Testing](#testing)
    - [Running Unit Tests](#running-unit-tests)
    *  [Testing configuration](#testing-configuration)
     * [Testing logger](#testing-logger)
- [Speed Report](#speed-report)
- [Uninstallation](#uninstallation)
- [Additional Notes](#additional-notes)
- [License](#license)

## Project Description

The `AlgoAssessment` project provides a TCP server that listens for incoming string queries. It searches a specified file for a full-line match of the query string. The server supports multithreading for handling multiple concurrent requests and can be configured with SSL authentication. The performance of multiple algorithms have been analyzed, tested, and compared to each other.

## Setup and Installation

### Prerequisites

*   **Python 3.10 or Higher**: Ensure that you have Python 3.10 or a higher version installed.
*   **Poetry:** Ensure that you have Poetry installed, if not, you can follow the instructions on [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation). You also need `openssl` installed on your system, for testing of SSL.
*   **Linux Environment**: This server is designed for Linux and assumes a Linux environment, as stated in the prompt. It was developed using `fish`, and tested on `bash`.

### Setting Up the Virtual Environment

1.  **Navigate to Project Root:**
    ```bash
    cd /path/to/your/project # Replace this with the path to your project
    ```
2.  **Create Virtual Environment (if needed)**:
    ```bash
    poetry env use python3.10
    poetry shell
    ```
    If you don't have an environment for this project, then Poetry will create a virtual environment automatically.

### Installing Dependencies

1.  **Install dependencies**:
    ```bash
    poetry install
    ```
    This command installs all dependencies from `pyproject.toml` (including dev dependencies).

### Alternative Method using `requirements.txt`
 If you would prefer not to use `poetry`, you can use a virtual environment using the `requirements.txt` file.

1.   **Create virtual environment**:
```bash
    python3 -m venv .venv
    source .venv/bin/activate
```
2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    This command will install all of the dependencies from the `requirements.txt` file.

## Project Structure

The project's folder structure is organized as follows:

```
.
├── config               # Example config file.
├── poetry.lock          # File to lock dependencies versions.
├── pyproject.toml        # Poetry configuration file.
├── README.md             # This file.
├── requirements.txt      # Requirements file
├── src                   # Source code for the application.
│   ├── client.py         # Client application.
│   ├── config.py         # Configuration module.
│   ├── logger.py         # Logging module.
│   ├── server.py         # Server application.
│   └── algorithms/       # Implemented searching algorithms.
│       ├── linear_search.py
│       ├── set_search.py
│       ├── mmap_search.py
│       ├── aho_corasick_search.py
│       ├── rabin_karp_search.py
│       ├── boyer_moore_search.py
│       ├── regex_search.py
│       └── multiprocessing_search.py
└── tests                 # Unit tests.
    ├── test_client.py    # Test cases for the client.
    ├── test_server.py    # Test cases for the server.
    └── test_config.py   # Test cases for the config.
    └── test_logger.py    # Test cases for the logger.

```

## Running the Server

The server can be run using the following command:

```bash
python core/server.py --config CONFIG_FILE [OPTIONS]
```

### Required Configuration

*   `--config CONFIG`: This argument is required. It specifies the path to the configuration file which contains the `linuxpath=...` parameter to the data file. This parameter must be present to start the server.

### Optional Server Configuration

The following are optional arguments, that can be used to modify how the server behaves.
*   `--server_config SERVER_CONFIG`: Specifies an extra configuration file for other server configuration parameters. If a setting is specified in both `--config` and `--server_config`, the value from `--server_config` will be used.
*   `--port PORT`: Specifies the port for the server to listen on.
*   `--ssl_enabled` : Set to `True` to enable SSL.
*   `--reread_on_query` : Set to `True` to reread the file on every query.
*   `--certfile CERTFILE` : Specifies the path to your SSL certificate.
*  `--keyfile KEYFILE` : Specifies the path to your SSL private key.

If the `--port` parameter is not specified, the server will search for a dynamically assigned port within the range of 44445 to 45445. The logs will show you what port was assigned.

### Using Dynamically Assigned Ports

If you choose not to specify a port, the server will automatically search for and use an available port in the range of 44445 to 45445. It will log a message indicating that a dynamic port has been assigned, and what the port is. This helps prevent port conflicts if other services or instances of the server are running.

### Running as a `systemd` Service

1.  **Create the `algo-server.service` File:**
    Create a file named `algo-server.service` with the following content, replacing the placeholders with your appropriate values.
    ```ini
    [Unit]
    Description=Algo Assessment Server
    After=network.target

    [Service]
    User=your_user  # Replace with your actual user
    WorkingDirectory=/path/to/your/project  # Replace with your actual project path
    ExecStart=/path/to/your/project/src/server.py --config /path/to/your/project/config.ini # Replace with your actual server path, and config
    Restart=on-failure
    # Add this line if you want to use a custom user to run the service.
    #User=your_username
    #Add this line if you want to use a custom group to run the service
    #Group=your_group

    [Install]
    WantedBy=multi-user.target
    ```
2.  **Copy the service file**: Run the following command (using sudo) to install the service:
    ```bash
        sudo ./install_server.sh
    ```
     This script will handle all of the necessary steps to set up the service.
3. **Reload systemd**: Run `sudo systemctl daemon-reload` to reload the systemd configuration.
4.  **Start the service**:  Use `sudo systemctl start algo-server.service` to start the server.
5.  **Enable the service**: Use `sudo systemctl enable algo-server.service` to enable the server so it will start automatically on boot.
6.  **Check Status:** Use `sudo systemctl status algo-server.service` to check if the service is running properly, or if there were any issues.

### Running as a Standalone Daemon

1.  **Use Provided `start.sh` Script:** Use the provided `start.sh` script from the root of the project:
    ```bash
    #!/bin/bash
    nohup python <path-to-project>/core/server.py --config <path-to-project>/core/config > <path-to-project>/core/server.log 2>&1 &
    echo "Server Started, check logs in <path-to-project>/core/server.log"
    ```
    where <path-to-project> is typicall `$(pwd)` so you can as well replace with this.

    Make sure to change the placeholder to the correct path to your project if it's not the current project directory.
2.  **Make it Executable:** Use `chmod +x start.sh` to make the file executable.
3.  **Start:** You can then run the server as a daemon using `./start.sh`, you can then check the logs in `server.log`.
4.  **Stop the server:** To stop the server you can run the provided stop script `stop.sh`, or use the command: `pkill -f <path>/core/server.py"`.

## Using the Client

The client can be run using the following command:

```bash
python src/client.py --query "your_query" [OPTIONS]
```

*   **Required:**
    *   `--query`:  The string query to search for in the data file.

*   **Optional:**
    *   `--client_config`:  The path to an optional client configuration file.
    *   `--server`:  Override the server ip address from the config file or defaults.
    *   `--port`: Override the server port from the config file or defaults.
    *   `--ssl_enabled`: Enable or disable SSL.
    *   `--cert_file`: Path to the SSL certificate file.
    *   `--key_file`: Path to the SSL key file.

If the server, or port are not specified in the client config, or command line, it will use default values, and report that it is using default values in the log.

## Testing

The project has unit tests to ensure that the code works as expected, and you can run these using the command:

```bash
pytest
```
This will run all of the test cases, and indicate if any tests are failing.

### Running Unit Tests

The unit tests are structured as follows:
*   **`tests/test_client.py`:** Contains tests for the client application and functionality.
*   **`tests/test_server.py`:** Contains tests for the server application and functionality.
*   **`tests/test_config.py`:** Contains tests for the config loading logic.
*   **`tests/test_logger.py`:**  Contains tests for the logging setup.

These tests can be run using the command `pytest`, from the project root, and it will pick up the files automatically, and execute them.

*   **Test Coverage**: The tests should cover the different cases of edge cases, missing configuration, invalid configuration, and also the valid behavior of the client and the server applications.
*   **Comprehensive Tests**: The tests should make sure that the core functionality works as expected, including all exception handling, logging, and all of the different command line parameters.

## Speed Report

The speed report is generated using the `core/speed_test.py` and will output the results in CSV files and the graph in a PDF. You can run the file using the command:
```bash
python core/speed_test.py
```
This will output three files: `speed_test_data_reread_true.csv`, `speed_test_data_reread_false.csv`, and `concurrency_test_data.csv`, in addition to the PDF `performance_graph.pdf`, with the performance graph.

The speed report (in PDF format) includes:

*   A detailed explanation of the testing environment and methodology.
*   A comparison of the performance of multiple file search algorithms.
*   Tables and a graph illustrating how the performance of algorithms changes with different file sizes and settings for `reread_on_query`
*    Tables and data for different levels of concurrency.
*   Analysis and conclusions about the different algorithms and their limitations.

## Uninstallation

To uninstall the server, you can use the provided uninstall script:

1.  **Run:** Execute the uninstall script (using sudo) from the project root directory:
    ```bash
    sudo ./uninstall_server.sh
    ```
    This will stop the service, disable it from starting on boot, and also delete the service file.

## Additional Notes

*   This code was developed using `fish`, and tested with bash.
*   Make sure you have the appropriate user access to run the script and perform install and uninstall tasks.
*   This README covers all of the basic use cases of the project, and it is very important to fully test this before submission.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.