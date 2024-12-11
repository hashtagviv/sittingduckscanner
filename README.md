# Sitting Duck Scanner

## Overview

The Sitting Duck Scanner is a web-based application designed to detect and analyze vulnerabilities in domain configurations, especially those that could lead to domain hijacking. It utilizes advanced tools like BBOT for subdomain enumeration and real-time monitoring to provide actionable insights into domain security.

The scanner primarily addresses the **sitting duck vulnerability**, which occurs when a domain's DNS provider service expires, even though the domain itself is still owned by the original registrar. This lapse creates a potential entry point for attackers to exploit expired domains or misconfigured name servers, leading to domain takeovers.

## Key Features

- **Real-Time Subdomain Scanning**: Dynamically identifies subdomains and examines their configurations.
- **Detailed Vulnerability Reporting**: Flags specific issues such as:
  - Lame delegation (misconfigured name servers).
  - Connectivity problems.
  - Registrar-DNS mismatches.
- **Asynchronous Processing**: Processes multiple domains and subdomains simultaneously to enhance efficiency.
- **User-Friendly Interface**: Provides a React-based frontend that allows users to initiate scans and track results in real-time.

## Purpose and Audience

- **Purpose**: The Sitting Duck Scanner is designed to support cybersecurity professionals, domain administrators, and developers in identifying and mitigating risks associated with domain-level vulnerabilities. By applying a structured algorithm, the scanner uncovers threats such as:
  - Inconsistencies between registrars and DNS providers.
  - Misconfigurations in name servers (e.g., lame delegation).
  - DNS providers susceptible to exploitation.
- **Audience**: The primary audience includes developers working on the system's backend or frontend  end-users utilizing the tool for domain security assessments.

## System Architecture

### High-Level Architecture Overview

The Sitting Duck Scanner consists of three core components:

1. **React Frontend**: Offers an intuitive user interface for initiating scans and monitoring real-time progress.
2. **FASTAPI Backend**: Serves as the central hub for processing scan requests, invoking Python-based logic, and streaming results to the frontend.
3. **Python Subdomain Scanner**: Implements the scanning algorithm using BBOT and other tools to identify vulnerabilities across subdomains.

### Workflow Description

#### React Frontend

- Users submit a domain and configure scanning options through the web application.
- The frontend continuously monitors the backend's `/stream` endpoint to retrieve and display real-time scan results.

#### FASTAPI Backend

- Receives domain scan requests via the `/start` endpoint.
- Initiates the Python-based scanning process and streams incremental results back to the frontend through the `/stream` endpoint.

#### Python Subdomain Scanner

- Conducts subdomain enumeration using BBOT and processes each discovered subdomain.
- Analyzes vulnerabilities, including:
  - Registrar-DNS mismatches.
  - Name server misconfigurations (e.g., lame delegation).
  - Exploitable DNS providers.

These components work together seamlessly, enabling users to view updates as they occur, ensuring a smooth and transparent scanning process.

## API Reference (via Swagger)

### Accessing the Swagger UI

The Sitting Duck Scanner includes a Swagger UI for interactive API documentation. This interface provides detailed information on available endpoints, request parameters, and response formats. To access the Swagger UI:

1. Start the FASTAPI backend by running `python main.py`.
2. Open a web browser and navigate to `http://localhost:8000/docs`.

### API Endpoints

#### POST `/start`

Initiates the scanning process for a given domain with user-specified parameters.

- **Request Body (JSON)**:
  ```json
  {
    "domain": "example.com",
    "email": "user@example.com",
    "related_domains": [".ca", ".org"],
    "time_limit": 100000,
    "active": 1
  }
  ```
- **Response**:
  - Returns a confirmation that the scanning process has started.

#### GET `/stream`

Streams the results of the scanning process in real time.

- **Request Parameters**: None
- **Response Format**:
  - Streams JSON objects line by line, with the following structure:
    ```json
    {
      "subdomain": "sub.example.com",
      "depth": 2,
      "lame_delegation": true,
      "registrar_dns_different": true,
      "flagged_name_servers": ["ns1.vulnerable.com"],
      "all_nameservers": ["ns1.example.com", "ns2.example.com"],
      "dns_providers": ["Provider1"],
      "registrar": "ExampleRegistrar",
      "connectivity": false,
      "issues": ["lame delegation detected"]
    }
    ```
  - Includes a final JSON object indicating the scan's completion:
    ```json
    {
      "status": "complete"
    }
    ```

## Installation and Setup

### Prerequisites

To run the Sitting Duck Scanner, ensure you have the following installed:

- **Python 3.9+**: Required for the backend and scanner logic.
- **Node.js and npm**: Required for the React frontend.

### Backend Setup

1. Navigate to the root directory of the project.
2. Install the required dependencies by running:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FASTAPI backend:
   ```bash
   python main.py
   ```
4. Access the Swagger UI at `http://localhost:8000/docs` to test the API.

### Frontend Setup

1. Navigate to the `my-app` directory.
2. Install the required dependencies by running:
   ```bash
   npm install
   ```
3. Start the React frontend:
   ```bash
   npm run start
   ```
4. Open `http://localhost:3000` in your browser to access the user interface.

### Combining Backend and Frontend

Run both the backend and frontend simultaneously to enable full functionality. Ensure the backend is accessible at `http://localhost:8000` for the frontend to fetch scan results.

##
