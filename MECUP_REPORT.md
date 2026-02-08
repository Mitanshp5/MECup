# MECup Application Technical Report

## 1. Project Overview
MECup is a hybrid desktop application designed for high-performance industrial control and real-time computer vision. It leverages a modern **split-process architecture**, combining a responsive **React-based frontend** for user interaction with a robust **Python backend** for hardware interfacing and AI inference.

## 2. Architecture
The application is built on a distributed system model running locally on the user's machine:

### A. Frontend (Renderer Process)
- **Role**: Handles all user interactions, visualizations, and state management.
- **Technology**: **React 18** running within an **Electron** container.
- **Communication**: Interacts with the backend via a RESTful API.
- **Key Features**:
    - **Real-time Updates**: Uses polling and efficient state management to display live hardware status (motor positions, sensor states).
    - **Dynamic UI**: Built with a component library (Shadcn/UI) and Tailwind CSS for a responsive, industrial-grade interface.
    - **Data Visualization**: Graphs and grids for visualizing inspection results and defects.

### B. Backend (Server Process)
- **Role**: The core logic engine, handling hardware communication, AI processing, and data persistence.
- **Technology**: **FastAPI (Python)** server.
- **Key Features**:
    - **Asynchronous Execution**: Detailed control of hardware (PLCs) without blocking the user interface.
    - **Concurrent Processing**: Runs heavy AI inference tasks in separate processes to maintain system responsiveness.
    - **Hardware Abstraction**: Provides a unified API to control diverse hardware (Motors, Cameras, Sensors).

## 3. Technology Stack Breakdown

### Frontend Technologies
| Technology | Usage | Benefit |
| :--- | :--- | :--- |
| **Electron** | Desktop Wrapper | Allows web technologies to run as a native desktop app with file system access. |
| **React 18** | UI Framework | Component-based architecture for building complex, interactive interfaces. |
| **TypeScript** | Language | Type safety ensures reliable code and fewer runtime errors. |
| **Vite** | Build Tool | Extremely fast development server and optimized production builds. |
| **Tailwind CSS** | Styling | Utility-first CSS for rapid, consistent, and responsive design. |
| **Shadcn/UI** | Component Library | Accessible, customizable components (based on Radix UI) for a professional look. |
| **React Query** | State Management | Efficiently manages server state, caching, and data synchronization. |
| **Framer Motion** | Animations | Smooth transitions and animations for a polished user experience. |

### Backend Technologies
| Technology | Usage | Benefit |
| :--- | :--- | :--- |
| **Python** | Core Language | Extensive ecosystem for AI, hardware control, and data processing. |
| **FastAPI** | Web Framework | High-performance, async-capable framework for building APIs. |
| **Uvicorn** | ASGI Server | Lightning-fast ASGI server implementation for Python. |
| **SQLAlchemy** | ORM | robust database abstraction layer for managing SQLite data. |
| **SQLite** | Database | Lightweight, serverless database ideal for local desktop applications. |

### Computer Vision & AI
| Technology | Usage | Benefit |
| :--- | :--- | :--- |
| **TensorRT** | Inference Backend | NVIDIA's high-performance deep learning inference optimizer (Primary). |
| **OpenVINO** | Inference Backend | Intel's toolkit for optimizing deep learning on Intel hardware (Secondary). |
| **ONNX Runtime** | Inference Backend | Cross-platform, high-performance inference engine (Fallback). |
| **OpenCV / Pillow**| Image Processing | Standard libraries for image manipulation and preprocessing. |
| **LangChain** | RAG Framework | Framework for building LLM-powered applications (Troubleshooting Agent). |
| **Ollama** | LLM Host | Locally runs large language models (e.g., Phi-3) for the RAG system. |
| **ChromaDB** | Vector Store | Stores embeddings for the RAG system to enable semantic search. |

### Hardware Communication
| Technology | Usage | Benefit |
| :--- | :--- | :--- |
| **MC Protocol** | PLC Protocol | Native communication protocol for Mitsubishi PLCs (`rk_mcprotocol` library). |
| **GenICam / SDK**| Camera Control | Industry-standard protocols for controlling industrial cameras. |

## 4. Feature Implementation Details

### A. Industrial Control System
- **PLC Integration**: The backend maintains a continuous connection to the Programmable Logic Controller (PLC). It uses a dedicated polling thread to monitor sensor inputs and register values in real-time.
- **Motion Control**: Implements logic to control servo motors (X, Y, Z axes) with variable speeds and precise positioning.
- **Safety Interlocks**: Software-enforced safety checks (e.g., ensuring servos are enabled before moving) prevent equipment damage.

### B. Automated Inspection Pipeline
1.  **Trigger**: The PLC signals the backend (via a specific register bit) when a product is in position.
2.  **Capture**: The backend triggers the industrial camera to capture a high-resolution image.
3.  **Inference**: The image is passed to the AI model (using TensorRT for maximum speed).
4.  **Analysis**: The capabilities include:
    - **Segmentation**: Identifying specific defect types (Dust, Scratches, etc.) at the pixel level.
    - **Classification**: Categorizing the product condition (Pass/Fail).
5.  **Actuation**: The system writes a result back to the PLC to trigger a sort mechanism (e.g., reject conveyor).

### C. Intelligent Troubleshooting (RAG)
- **Concept**: A Retrieval-Augmented Generation (RAG) system designed to assist operators.
- **Mechanism**:
    - **Knowledge Base**: Technical manuals and error codes are indexed in a vector database (ChromaDB).
    - **Querying**: Operators can ask natural language questions (e.g., "Why is the X-axis stalled?").
    - **Response**: The system retrieves relevant context and uses a local LLM (Phi-3 via Ollama) to generate a helpful solution.

## 5. Security Architecture
- **In-App Authentication**: Implementation of JWT (JSON Web Tokens) for managing user sessions.
- **Role-Based Access Control (RBAC)**: Distinct permissions for different user roles (e.g., strict limits on `viewer` accounts vs full control for `admin`).
- **Local Execution**: All processing (AI, Database, Control) occurs locally, ensuring data privacy and operational security without cloud dependencies.
