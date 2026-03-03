<p align="center">
  <img src="public/assets/MECUP_logo.png" alt="CON-SOL-E Vision Pro" width="180"/>
</p>

<h1 align="center">CON-SOL-E Vision Pro</h1>

<p align="center">
  <strong>AI-Powered Industrial Paint Defect Detection & Quality Control System</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=white" alt="React"/>
  <img src="https://img.shields.io/badge/TypeScript-5.8-3178C6?logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/Electron-39-47848F?logo=electron&logoColor=white" alt="Electron"/>
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/OpenVINO-2024-0071C5?logo=intel&logoColor=white" alt="OpenVINO"/>
  <img src="https://img.shields.io/badge/DINOv2-ViT--B14-FF6F00?logo=pytorch&logoColor=white" alt="DINOv2"/>
  <img src="https://img.shields.io/badge/LangChain-RAG-1C3C3C?logo=langchain&logoColor=white" alt="LangChain"/>
</p>

<p align="center">
  A full-stack desktop application for <strong>real-time automated visual inspection</strong> of painted automotive door panels on a CNC gantry system. Combines deep learning segmentation, PLC-driven motion control, industrial camera integration, and an AI-powered troubleshooting assistant — all running locally with zero cloud dependency.
</p>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [AI & Computer Vision Pipeline](#ai--computer-vision-pipeline)
- [Application Pages](#application-pages)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Hardware Requirements](#hardware-requirements)
- [Contributors](#contributors)
- [License](#license)

---

## Overview

**CON-SOL-E Vision Pro** is an end-to-end industrial quality control platform built for a real-world manufacturing environment. A CNC gantry moves an industrial camera across a painted door panel in a grid pattern, capturing high-resolution images at each position. Each image is analyzed in real-time by a **DINOv2-based semantic segmentation model** (optimized with Intel OpenVINO) to detect and classify paint defects — **Dust**, **Scratch**, and **Rundown** — at the pixel level.

The system provides:
- **Real-time defect detection** with sub-second inference on consumer hardware
- **Automated scan cycles** orchestrated via Mitsubishi PLC over MC Protocol
- **Stitched panoramic views** and **defect heatmaps** of entire door panels
- **PDF inspection reports** with vision analytics and process recommendations
- **AI troubleshooting chatbot** powered by a local RAG system (Phi-3 + ChromaDB)
- **Mobile companion app** for remote monitoring on the factory floor
- **Role-based access control** with JWT authentication

Everything runs **100% locally** — no internet, no cloud, no data leaves the factory.

---

## Key Features

### Automated Inspection
- **Grid-based scanning** — CNC gantry moves camera across X/Y/Z axes in a configurable grid pattern
- **Real-time inference** — Each captured image is processed through DINOv2 segmentation in <500ms
- **Defect classification** — Pixel-level detection of Dust, Scratch, and Rundown defects
- **Pass/Fail determination** — Automatic quality verdict based on defect area thresholds
- **Background report generation** — Stitching and heatmap generation triggered automatically on cycle completion without blocking the UI

### Hardware Control
- **PLC Integration** — Direct communication with Mitsubishi PLCs via MC Protocol (TCP binary)
- **3-Axis Motion Control** — Precise servo motor control with real-time position feedback (X, Y, Z in mm)
- **Industrial Camera** — HIKROBOT MVS SDK integration with configurable exposure, gain, and triggering
- **LED Lighting** — Programmable illumination modes (White/Green) with directional control (Up/Down/Left/Right)
- **Safety Systems** — Emergency stop monitoring (M599), servo enable interlocks, and homing sequences

### AI-Powered Troubleshooting
- **RAG Chatbot** — Natural language troubleshooting assistant embedded in the UI
- **Local LLM** — Phi-3 running via Ollama, completely offline
- **Vector Search** — ChromaDB with BGE embeddings indexes technical manuals and error code documentation
- **345 Hardcoded Error Codes** — Instant lookup for known servo alarm codes with structured troubleshooting steps
- **Conversation History** — Session-based multi-turn conversations with context preservation

### Reporting & Analytics
- **Image Stitching** — Weighted blending of grid images into a single panoramic view of the door panel
- **Defect Heatmaps** — Gaussian-smoothed density maps highlighting defect concentration zones
- **PDF Reports** — Printable inspection reports with defect breakdowns, vision analytics, and process recommendations
- **Intensive Summary** — Statistical analysis of defect distributions across the scanned surface
- **Scan History** — Browse, search, filter, and delete past inspection records

### System Health Monitoring
- **Real-time Heartbeat** — Live servo position charts (X, Y, Z) with daily min/max tracking
- **System Resources** — CPU, GPU, Memory, and Disk usage monitoring
- **Component Status** — Camera, lights, motors, PLC connection health at a glance
- **Global Emergency Popup** — Full-screen alert when emergency stop is triggered

### Mobile Companion
- **Responsive Mobile UI** — Dedicated pages optimized for tablets and phones on the factory floor
- **Remote Monitoring** — View system health, scan reports, and defect details from any device on the LAN
- **Mobile Authentication** — Secure login with the same JWT-based auth system

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ELECTRON DESKTOP APP                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              React 18 + TypeScript Frontend            │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │  │
│  │  │Dashboard │ │Automatic │ │  Manual  │ │ Scans &  │ │  │
│  │  │  + 3D    │ │   Mode   │ │   Mode   │ │ Reports  │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │  │
│  │  │Heartbeat │ │ Settings │ │  Users   │ │ Chatbot  │ │  │
│  │  │  Health  │ │  Panel   │ │  Mgmt    │ │  (RAG)   │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │  │
│  └──────────────────────┬────────────────────────────────┘  │
│                         │ REST API (port 5001)               │
│  ┌──────────────────────▼────────────────────────────────┐  │
│  │               FastAPI Python Backend                   │  │
│  │  ┌──────┐ ┌──────────┐ ┌────────┐ ┌───────────────┐  │  │
│  │  │ Auth │ │   PLC    │ │ Camera │ │   Inference    │  │  │
│  │  │ JWT  │ │MC Proto  │ │MVS SDK │ │  OpenVINO +   │  │  │
│  │  │ RBAC │ │ Polling  │ │ GigE   │ │  DINOv2 ViT   │  │  │
│  │  └──────┘ └──────────┘ └────────┘ └───────────────┘  │  │
│  │  ┌──────────────┐  ┌──────────────────────────────┐   │  │
│  │  │  RAG Agent   │  │     Utils & Services         │   │  │
│  │  │ Phi-3 + BGE  │  │ Stitcher, Heatmap, Reports   │   │  │
│  │  │  ChromaDB    │  │ Background Thread Workers     │   │  │
│  │  └──────────────┘  └──────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────▼────┐         ┌────▼────┐          ┌────▼────┐
    │Mitsubishi│         │HIKROBOT │          │  SQLite │
    │  PLC    │         │ Camera  │          │   DB    │
    │(MC TCP) │         │ (GigE)  │          │ (Local) │
    └─────────┘         └─────────┘          └─────────┘
```

---

## Tech Stack

### Frontend
| Technology | Purpose |
|:---|:---|
| **React 18** | Component-based UI framework |
| **TypeScript** | Type-safe development |
| **Electron 39** | Native desktop wrapper with backend process management |
| **Vite 5** | Lightning-fast HMR dev server and optimized builds |
| **Tailwind CSS 3** | Utility-first styling with custom industrial dark theme |
| **Shadcn/UI + Radix** | 49 accessible, customizable UI components |
| **Framer Motion** | Smooth animations and transitions |
| **React Query** | Server state management with polling |
| **Recharts** | Real-time data visualization and charts |
| **React Three Fiber** | 3D model rendering on the dashboard (Three.js) |
| **html2pdf.js** | Client-side PDF report generation |

### Backend
| Technology | Purpose |
|:---|:---|
| **Python 3.10+** | Core backend language |
| **FastAPI** | High-performance async REST API framework |
| **Uvicorn** | ASGI server |
| **SQLAlchemy + SQLite** | ORM and local database for users, scans, stats |
| **Passlib + python-jose** | JWT authentication with bcrypt password hashing |
| **Threading** | Background workers for non-blocking report generation |

### AI & Computer Vision
| Technology | Purpose |
|:---|:---|
| **DINOv2 ViT-B/14** | Frozen vision transformer encoder for feature extraction |
| **Multi-Scale CNN Decoder** | Trainable decoder with skip connections for segmentation |
| **Intel OpenVINO 2024** | Hardware-optimized inference (CPU/GPU) with model caching |
| **OpenCV + Pillow + NumPy** | Image preprocessing, stitching, heatmap generation |
| **SciPy** | Connected component analysis for defect instance counting |

### RAG System
| Technology | Purpose |
|:---|:---|
| **LangChain + LangGraph** | Agent orchestration with stateful graph execution |
| **Ollama (Phi-3)** | Local LLM inference, fully offline |
| **ChromaDB** | Persistent vector store for document embeddings |
| **BGE-base-en-v1.5** | HuggingFace sentence embeddings for semantic search |

### Hardware Communication
| Technology | Purpose |
|:---|:---|
| **MC Protocol (TCP Binary)** | Native Mitsubishi PLC communication via `rk_mcprotocol` |
| **HIKROBOT MVS SDK** | Industrial GigE camera control and image acquisition |
| **psutil + WMI** | System resource monitoring (CPU, GPU, Memory, Disk) |

---

## AI & Computer Vision Pipeline

### Model Architecture

```
Input Image (518x518)
        │
        ▼
┌─────────────────────┐
│  DINOv2 ViT-B/14    │  Frozen encoder - pretrained vision transformer
│  (Patch size: 14)   │  Extracts features at layers [3, 7, 11]
└─────┬───┬───┬───────┘
      │   │   │  Skip connections
      ▼   ▼   ▼
┌─────────────────────┐
│  Multi-Scale Decoder │  Trainable CNN decoder
│  [256, 128, 64] ch  │  Progressive upsampling with skip fusion
│  + Dropout (0.1)    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Segmentation Head   │  Per-pixel classification
│  4 classes:          │  Background | Dust | Rundown | Scratch
└─────────────────────┘
```

### Inference Pipeline
1. **Capture** — Industrial camera captures 518x518px image at grid position
2. **Preprocess** — Resize, normalize (ImageNet stats), layout conversion (NHWC→NCHW)
3. **Infer** — OpenVINO compiled model runs on GPU (preferred) or CPU with latency optimization
4. **Postprocess** — Argmax segmentation mask + softmax confidence maps
5. **Analyze** — Connected component analysis counts individual defect instances, calculates area ratios
6. **Report** — JSON report with per-class pixel counts, area percentages, severity ratings, and overlay images

### Supported Defect Types
| Defect | Description | Severity Thresholds |
|:---|:---|:---|
| **Dust** | Particulate contamination trapped in paint | Area-based |
| **Scratch** | Linear surface damage to paint finish | Area-based |
| **Rundown** | Paint drip/sag caused by over-application | Area-based |

---

## Application Pages

### Desktop Application

| Page | Description |
|:---|:---|
| **Dashboard** | Interactive 3D model viewer, system stats, quick-access cards, role-based greeting |
| **Automatic Mode** | Full automated scan cycle — start/stop/reset, real-time inference results, defect grid, model selection (White/Black) |
| **Manual Mode** | Jog controls for X/Y/Z axes, LED lighting panel (White/Green + directional), servo enable/disable, homing |
| **Past Scans** | Searchable scan history with detail views, stitched images, heatmaps, and PDF report generation |
| **Heartbeat** | Live servo position charts (X, Y, Z), daily min/max statistics, component health dashboard |
| **Settings** | PLC connection config (IP/Port), camera settings (Exposure/Gain), stitch scale, theme toggle |
| **User Management** | Admin panel for creating/editing/deleting users with role assignment (Admin/Operator/Viewer) |

### Mobile Companion

| Page | Description |
|:---|:---|
| **Mobile Dashboard** | Simplified scan overview optimized for touch devices |
| **Mobile Health** | System component status and servo charts for factory floor monitoring |
| **Mobile Report** | View and export scan reports from any device on the network |

---

## Project Structure

```
MECup/
├── electron/
│   └── main.js                  # Electron main process - spawns backend, creates window
├── src/                         # React frontend source
│   ├── pages/                   # 13 page components (Desktop + Mobile)
│   ├── components/
│   │   ├── chatbot/             # RAG chatbot UI
│   │   ├── reports/             # PrintableReport + ScanReport components
│   │   ├── layout/              # AppLayout, Sidebar, TopBar
│   │   ├── ui/                  # 49 Shadcn/UI components
│   │   ├── GlobalEmergencyPopup.tsx
│   │   ├── ProtectedRoute.tsx   # RBAC route guards
│   │   └── LoginModal.tsx
│   ├── context/
│   │   └── AuthContext.tsx       # JWT auth state management
│   ├── hooks/                   # Custom React hooks
│   └── lib/                     # API config, utilities
├── backend/
│   ├── main.py                  # FastAPI app entrypoint (port 5001)
│   ├── mobile_main.py           # Standalone mobile API server
│   ├── database.py              # SQLAlchemy engine + session
│   ├── auth/                    # JWT auth module (router, models, security)
│   ├── plc/
│   │   ├── connection.py        # PLCManager singleton (MC Protocol TCP)
│   │   ├── endpoints.py         # 30+ PLC/scan/control endpoints
│   │   ├── scan_manager.py      # ScanSession state machine
│   │   ├── mc_protocol_fixed.py # MC Protocol binary implementation
│   │   └── settings.py          # PLC config persistence
│   ├── camera/
│   │   ├── camera_manager.py    # HIKROBOT MVS SDK wrapper
│   │   └── endpoints.py         # Camera control API
│   ├── inference/
│   │   ├── inference_service.py # DefectPredictor - OpenVINO inference engine
│   │   ├── endpoints.py         # Inference API + batch processing
│   │   └── convert_model.py     # PyTorch → OpenVINO IR converter
│   ├── models/
│   │   ├── model.py             # SegmentationModel (DINOv2 + Decoder)
│   │   ├── encoder.py           # DINOv2Encoder with skip connections
│   │   └── decoder.py           # MultiScaleDecoder with progressive upsampling
│   ├── production_rag/
│   │   ├── agent_improved.py    # RAG agent + 345 hardcoded error codes
│   │   ├── fastapi_server.py    # Troubleshoot API endpoints
│   │   └── rebuild_vectordb.py  # PDF → ChromaDB indexing
│   └── utils/
│       └── image_stitcher.py    # Panoramic stitching + heatmap generation
├── public/assets/
│   ├── DoorChecker.glb          # 3D model for dashboard
│   └── MECUP_logo.png           # Application logo
├── package.json                 # Frontend dependencies + Electron build config
├── vite.config.ts               # Vite build configuration
├── tailwind.config.ts           # Custom theme (industrial dark palette)
└── tsconfig.json                # TypeScript configuration
```

---

## Getting Started

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.10+
- **Ollama** with `phi3` model pulled (for RAG chatbot)
- Intel GPU recommended (for OpenVINO GPU inference)

### Installation

```bash
# Clone the repository
git clone https://github.com/Mitanshp5/MECup.git
cd MECup

# Install frontend dependencies
npm install

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### Running in Development

```bash
# Terminal 1: Start the backend
cd backend
python main.py

# Terminal 2: Start the frontend dev server
npm run dev
```

### Running as Electron Desktop App

```bash
# Development mode (with hot reload)
npm run electron

# Production build
npm run electron:build
```

### Environment Variables

Create `backend/.env`:
```env
MECUP_ADMIN_USER=admin
MECUP_ADMIN_PASSWORD=your_password
SECRET_KEY=your_random_secret_key
```

### Setting Up the RAG System

```bash
# Pull the LLM model
ollama pull phi3

# Index documentation into vector database
cd backend/production_rag
python rebuild_vectordb.py
```

---

## Hardware Requirements

### Minimum (Development)
- **CPU**: Intel i5 8th Gen or equivalent
- **RAM**: 8 GB
- **GPU**: Intel UHD 630 (for OpenVINO inference)
- **Storage**: 2 GB free

### Recommended (Production)
- **CPU**: Intel i7 12th Gen or newer
- **RAM**: 16 GB
- **GPU**: Intel Iris Xe or Arc (OpenVINO GPU acceleration)
- **Storage**: 10 GB+ (for scan image storage)
- **PLC**: Mitsubishi FX5U or compatible (MC Protocol TCP)
- **Camera**: HIKROBOT GigE industrial camera
- **Network**: Gigabit Ethernet (for PLC and camera communication)

---

## Contributors

<table>
  <tr>
      <td align="center">
      <a href="https://github.com/Priyanshu-byte-coder">
        <strong>Priyanshu Doshi</strong>
      </a>
      <br />
    </td>
    <td align="center">
      <a href="https://github.com/Mitanshp5">
        <strong>Mitansh Prajapati</strong>
      </a>
      <br />
    </td>

  </tr>
</table>

---

## License

This project is proprietary and developed for industrial use. All rights reserved.

---

<p align="center">
  <sub>Built with precision for the factory floor.</sub>
</p>
