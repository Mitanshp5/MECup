# Paint Defect Detection System - Technical Support Agent

## Overview

This RAG (Retrieval-Augmented Generation) agent is a specialized technical support assistant designed exclusively for **industrial paint job defect detection systems**. It serves as an intelligent troubleshooting and technical guidance tool for operators, technicians, and maintenance personnel.

## Primary Purpose

**Troubleshooting System Problems**

The agent's main function is to diagnose and resolve issues that occur in the paint defect detection system, including:
- Component failures and malfunctions
- Error codes and fault conditions
- Performance degradation
- Calibration issues
- Integration problems between components

## Secondary Purpose

**General Technical Support**

While troubleshooting is the primary focus, the agent can also assist with:
- System operation questions
- Configuration guidance
- Maintenance procedures
- Best practices
- Technical specifications

## System Components Covered

The agent has comprehensive documentation for all system components:

### 1. **Vision Cameras & Imaging Systems**
- Camera hardware specifications
- Image capture settings
- Lens calibration
- Lighting conditions
- Image quality issues (oversaturation, underexposure, blur)
- Camera positioning and alignment

### 2. **Defect Detection Algorithms**
- Detection parameters and thresholds
- Algorithm configuration
- False positive/negative troubleshooting
- Sensitivity adjustments
- Defect classification (scratches, dust, rundown, etc.)

### 3. **PLC Controllers & Automation**
- PLC programming and logic
- I/O configuration
- Communication protocols
- Timing and synchronization
- Automation sequences

### 4. **Error Codes & Fault Diagnostics**
- System error codes (e.g., 19A6H, 1A68H)
- Component-specific error messages
- Diagnostic procedures
- Root cause analysis
- Recovery procedures

### 5. **Calibration & Maintenance**
- Routine maintenance schedules
- Calibration procedures
- Preventive maintenance
- Component replacement
- System validation

### 6. **Paint Application Quality**
- Paint defect types and causes
- Surface preparation issues
- Application technique problems
- Environmental factors
- Quality control procedures

## How It Works

### Knowledge Base
The agent uses a vector database containing:
- Component manuals and datasheets
- Troubleshooting guides
- Error code references
- Maintenance procedures
- Technical specifications
- Best practice documents

### Intelligent Retrieval
When you ask a question, the agent:
1. Analyzes your query to understand the problem
2. Searches through all component documentation
3. Retrieves the most relevant information
4. Generates a structured, actionable response
5. Maintains conversation context for follow-up questions

### Response Format
Responses are formatted in HTML with clear sections:
- **Issue Identified**: What the problem is
- **Troubleshooting Steps**: Numbered, actionable steps to resolve it
- **Additional Notes**: Warnings, tips, or related information

## Use Cases

### Troubleshooting Scenarios
```
✓ "Error code 19A6H appeared on the display"
✓ "Camera is not detecting scratches properly"
✓ "System keeps giving false positives for dust"
✓ "PLC communication timeout errors"
✓ "Vision system shows oversaturated images"
✓ "Defect detection stopped working after maintenance"
```

### Technical Questions
```
✓ "How do I calibrate the vision camera?"
✓ "What are the optimal lighting settings?"
✓ "How often should I perform maintenance?"
✓ "What does the light intensity parameter control?"
✓ "How do I adjust detection sensitivity?"
```

### Follow-up Conversations
```
User: "What is error 19A6H?"
Agent: [Explains the error]

User: "How do I fix it?"
Agent: [Provides steps, remembering context]

User: "What causes this error?"
Agent: [Explains root causes, still in context]
```

## Key Features

### 1. **Context-Aware**
- Remembers previous questions in the conversation
- Understands follow-up queries
- Maintains topic continuity

### 2. **Component-Specific**
- Draws from documentation of each system component
- Provides accurate, source-based answers
- References specific manuals when needed

### 3. **Actionable Guidance**
- Structured troubleshooting steps
- Clear, concise instructions
- Prioritized actions

### 4. **Multi-Session Support**
- Separate conversations for different users
- Session-based history tracking
- Isolated contexts per session

## What the Agent Can Do

✅ **Diagnose error codes** - Explain what they mean and how to fix them
✅ **Troubleshoot component failures** - Guide through diagnostic procedures
✅ **Provide maintenance guidance** - Explain procedures and schedules
✅ **Answer technical questions** - Clarify system operation and parameters
✅ **Suggest solutions** - Offer multiple approaches to problems
✅ **Remember context** - Handle follow-up questions naturally
✅ **Reference documentation** - Base answers on actual component manuals

## What the Agent Cannot Do

❌ **Diagnose issues outside the system** - Only covers paint defect detection components
❌ **Provide real-time system status** - No direct connection to live system
❌ **Execute commands** - Cannot control or configure the system directly
❌ **Replace human expertise** - Should supplement, not replace, trained technicians
❌ **Guarantee solutions** - Some issues may require manufacturer support

## Best Practices for Using the Agent

### Be Specific
```
❌ "Camera not working"
✅ "Camera is not capturing images, showing black screen"

❌ "Error on display"
✅ "Error code 19A6H displayed after system restart"
```

### Provide Context
```
✅ "After calibration, the system detects too many false positives"
✅ "This started happening after we replaced the camera lens"
✅ "The issue only occurs when paint is dark colored"
```

### Use Follow-ups
```
First: "What is error 19A6H?"
Then: "What causes it?"
Then: "How do I prevent it in the future?"
```

### Specify Components
```
✅ "Vision camera shows oversaturated images"
✅ "PLC communication timeout with defect detection module"
✅ "Scratch detection algorithm missing small defects"
```

## Integration

The agent integrates with the MECup backend system and is accessible via:
- REST API endpoints (`/api/troubleshoot`)
- Web interface (chat interface)
- Mobile application support

## Documentation Sources

The agent's knowledge comes from:
- Official component manuals
- Manufacturer troubleshooting guides
- Error code reference documents
- Maintenance procedure documents
- Technical specification sheets
- Best practice guidelines

All responses are grounded in this documentation, ensuring accuracy and reliability.

## Target Users

- **System Operators** - Day-to-day operation and basic troubleshooting
- **Maintenance Technicians** - Routine maintenance and component replacement
- **Field Engineers** - Advanced troubleshooting and system optimization
- **Quality Control Personnel** - Understanding defect detection parameters
- **Training Staff** - Learning system operation and troubleshooting

## Summary

This agent is your **first line of technical support** for the paint defect detection system. It provides instant, accurate, and actionable guidance for troubleshooting problems and answering technical questions about all system components. While it's designed primarily for problem-solving, it can also assist with general technical inquiries about system operation, making it a versatile tool for anyone working with the paint defect detection system.
