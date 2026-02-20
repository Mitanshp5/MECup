"""
Production RAG Agent - Improved Accuracy Version
Implements: Query expansion, hybrid retrieval, better chunking awareness
"""

from typing import TypedDict, List, Tuple, Dict
import os
import re

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VECTORDB_DIR = os.path.join(SCRIPT_DIR, "vectordb")
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
LLM_MODEL = "phi3"

# Optimized retrieval settings for 500-page corpus
TOP_K = 8  # Increased for better coverage with smaller corpus
RELEVANCE_THRESHOLD = 0.1  # Lower threshold for more inclusive retrieval
FETCH_K = 16  # Larger candidate pool for better selection

# Auto-generated error code database
# Generated from PDF documentation

# Hardcoded error codes extracted from servo manual PDFs
# Hardcoded error codes extracted from servo manual PDFs
# Hardcoded error codes extracted from servo manual PDFs
ERROR_CODE_DATABASE = {
    "10": {
        "name": "Undervoltage",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 10 - Undervoltage:  The voltage of the control circuit power supply has dropped.  The voltage of the main circuit power supply has dropped</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify power supply voltage is within specifications.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "11": {
        "name": "Switch setting error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 11 - Switch setting error:  The setting of the axis selection rotary switch or auxiliary axis number setting switch is incorrect.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "12": {
        "name": "Memory error 1 (RAM)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 12 - Memory error 1 (RAM):  A part (RAM) in the servo amplifier is failure</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "13": {
        "name": "Clock error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 13 - Clock error:  A part in the servo amplifier is failure.  A clock error transmitted from the controller occurred.  [RJ010]: MR-J3-T10 came off</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check method: Check res...</li>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "14": {
        "name": "Control process error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 14 - Control process error:  The process did not complete within the specified time.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "15": {
        "name": "Memory error 2 (EEP-ROM)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 15 - Memory error 2 (EEP-ROM):  A part (EEP-ROM) in the servo amplifier is failure.  [RJ010]: MR-J3-T10 came off</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Verify power supply voltage is within specifications.</li>
    </ol>
  </div>
</div>"""
    },
    "16": {
        "name": "Encoder initial communication error 1",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 16 - Encoder initial communication error 1:  An error occurred in the communication between an encoder and servo amplifier</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "17": {
        "name": "Board error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 17 - Board error:  A part in the servo amplifier is malfunctioning</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "19": {
        "name": "Memory error 3 (Flash-ROM)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 19 - Memory error 3 (Flash-ROM):  A part (Flash-ROM) in the servo amplifier is failure</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "20": {
        "name": "Encoder normal communication error 1",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 20 - Encoder normal communication error 1:  An error occurred in the communication between an encoder and servo amplifier</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "21": {
        "name": "Encoder normal communication error 2",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 21 - Encoder normal communication error 2:  The encoder detected an error signal</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "24": {
        "name": "Main circuit error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 24 - Main circuit error:  A ground fault occurred on the servo motor power lines.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify power supply voltage is within specifications.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "25": {
        "name": "Absolute position erased",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 25 - Absolute position erased:  The absolute position data is faulty.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify power supply voltage is within specifications.</li>
    </ol>
  </div>
</div>"""
    },
    "27": {
        "name": "Initial magnetic pole detection error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 27 - Initial magnetic pole detection error:  The initial magnetic pole detection was not completed properly</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "28": {
        "name": "Linear encoder error 2",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 28 - Linear encoder error 2:  Working environment of linear encoder is not normal</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "30": {
        "name": "Regenerative error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 30 - Regenerative error:  Permissible regenerative power of the built-in regenerative resistor or regenerative option is exceeded.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Verify power supply voltage is within specifications.</li>
    </ol>
  </div>
</div>"""
    },
    "31": {
        "name": "Overspeed",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 31 - Overspeed:  The servo motor speed has exceeded the instantaneous permissible speed.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "32": {
        "name": "Overcurrent",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 32 - Overcurrent:  A current higher than the permissible current was applied to the servo amplifier</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "33": {
        "name": "Overvoltage",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 33 - Overvoltage:  The value of the bus voltage exceeded the prescribed value.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify power supply voltage is within specifications.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "34": {
        "name": "SSCNET receive error 1",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 34 - SSCNET receive error 1:  An error occurred in SSCNET /H communication. (continuous communication error with 3.5 ms interval)</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "35": {
        "name": "Command frequency error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 35 - Command frequency error:  Input pulse frequency of command pulse is too high</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "36": {
        "name": "SSCNET receive error 2",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 36 - SSCNET receive error 2:  An error occurred in SSCNET /H communication. (intermittent communication error with about 70 ms interval)</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "37": {
        "name": "Parameter error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 37 - Parameter error:  Parameter setting is incorrect.  Point table setting is incorrect</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "39": {
        "name": "Program error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 39 - Program error:  A program used for the program operation is incorrect</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "42": {
        "name": "Servo control error (for linear servo motor and direct drive motor)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 42 - Servo control error (for linear servo motor and direct drive motor):  A servo control error occurred</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "45": {
        "name": "Main circuit device overheat",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 45 - Main circuit device overheat:  Inside of the servo amplifier overheated</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
    </ol>
  </div>
</div>"""
    },
    "46": {
        "name": "Servo motor overheat",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 46 - Servo motor overheat:  The servo motor overheated</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "47": {
        "name": "Cooling fan error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 47 - Cooling fan error:  The speed of the servo amplifier cooling fan decreased.  Or the fan speed decreased to the alarm occurrence level or less</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "50": {
        "name": "Overload 1",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 50 - Overload 1:  Load exceeded overload protection characteristic of servo amplifier</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "51": {
        "name": "Overload 2",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 51 - Overload 2:  Maximum output current flowed continuously due to machine collision or the like</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "52": {
        "name": "Error excessive",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 52 - Error excessive:  Droop pulses have exceeded the alarm occurrence level</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify power supply voltage is within specifications.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "54": {
        "name": "Oscillation detection",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 54 - Oscillation detection:  An oscillation of the servo motor was detected</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "56": {
        "name": "Forced stop error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 56 - Forced stop error:  The servo motor does not decelerate normally during forced stop deceleration</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "61": {
        "name": "Operation error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 61 - Operation error:  An operation of the positioning function failed</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "63": {
        "name": "STO timing error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 63 - STO timing error:  STO input signal turns off while the servo motor is rotating</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "64": {
        "name": "Functional safety unit setting error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 64 - Functional safety unit setting error:  A setting of the servo amplifier or functional safety unit was incorrect</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "65": {
        "name": "Functional safety unit connection error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 65 - Functional safety unit connection error:  Communication or signal between a functional safety unit and servo amplifier failed</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "66": {
        "name": "Encoder initial communication error (safety observation function)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 66 - Encoder initial communication error (safety observation function):  The connected encoder is not compatible with the servo amplifier.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "67": {
        "name": "Encoder normal communication error 1 (safety observation function)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 67 - Encoder normal communication error 1 (safety observation function):  An error has occurred in the communication between an encoder and servo amplifier</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "68": {
        "name": "STO diagnosis error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 68 - STO diagnosis error:  An error of STO input signal was detected</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "69": {
        "name": "Command error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 69 - Command error:  The command position exceeded 32 bits (-2147483648 to 2147483647) when the software limit is activated.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "70": {
        "name": "Load-side encoder initial communication error 1",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 70 - Load-side encoder initial communication error 1:  An error occurred in the initial communication between the load-side encoder and servo amplifier</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "71": {
        "name": "Load-side encoder normal communication error 1",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 71 - Load-side encoder normal communication error 1:  An error occurred in the communication between the load-side encoder and servo amplifier</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "72": {
        "name": "Load-side encoder normal communication error 2",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 72 - Load-side encoder normal communication error 2:  The load-side encoder detected an error signal</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "74": {
        "name": "Option card error 1",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 74 - Option card error 1:  MR-J3-T10 came off.  MR-J3-T10 is not properly recognized</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "75": {
        "name": "Option card error 2",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 75 - Option card error 2:  MR-J3-T10 came off</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "79": {
        "name": "Functional safety unit diagnosis error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 79 - Functional safety unit diagnosis error:  A diagnosis of the functional safety unit failed</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify power supply voltage is within specifications.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "82": {
        "name": "Master-slave operation error 1",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 82 - Master-slave operation error 1:  Driver communication error was detected</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "84": {
        "name": "Network module initialization error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 84 - Network module initialization error:  The network module is not connected.  An error occurred at initialization of the network module</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "85": {
        "name": "Network module error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 85 - Network module error:  The network module was disconnected.  An error occurred in the network module. (Refer to section 1.7.)</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "86": {
        "name": "Network communication error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 86 - Network communication error:  An error occurred in the network module.  An error occurred in the network communication</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "90": {
        "name": "Home position return incomplete warning",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 90 - Home position return incomplete warning:  Home position return has not been finished.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "91": {
        "name": "Servo amplifier overheat warning",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 91 - Servo amplifier overheat warning:  The temperature inside of the servo amplifier reached a warning level</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
    </ol>
  </div>
</div>"""
    },
    "92": {
        "name": "Battery cable disconnection warning",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 92 - Battery cable disconnection warning:  Battery voltage for absolute position detection system decreased</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify power supply voltage is within specifications.</li>
    </ol>
  </div>
</div>"""
    },
    "93": {
        "name": "ABS data transfer warning",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 93 - ABS data transfer warning:  ABS data were not transferred</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "95": {
        "name": "STO warning",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 95 - STO warning:  STO input signal turns off while the servo motor stops.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "96": {
        "name": "Home position setting warning",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 96 - Home position setting warning:  Home position setting could not be made</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "97": {
        "name": "Positioning specification warning",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 97 - Positioning specification warning:  How to specify a positioning is incorrect for the positioning function</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "98": {
        "name": "Software limit warning",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 98 - Software limit warning:  A software limit set with the parameter was reached for the positioning function</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "99": {
        "name": "Stroke limit warning",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 99 - Stroke limit warning:  The stroke limit signal is off</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "e0": {
        "name": "Excessive regeneration warning]",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm e0 - Excessive regeneration warning]: • [AL. E1 Overload warning 1] • [AL.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "e1": {
        "name": "Overload warning 1]",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm e1 - Overload warning 1]: • [AL. E2 Servo motor overheat warning] • [AL.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "e2": {
        "name": "Servo motor overheat warning]",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm e2 - Servo motor overheat warning]: • [AL. EC Overload warning 2] Warnings (except [AL.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "e5": {
        "name": ".1].",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm e5 - .1].: E5.3 SON off during ABS data transfer Alarm No.: E6 Name: Servo forced stop warning Alarm content  EM2/EM1 (Forced stop) turned off.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Identify the cause: Check...</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "e8": {
        "name": ".1].",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm e8 - .1].: Alarm No.: E9 Name: Main circuit off warning Alarm content  The servo-on command was inputted with main circuit power supply off.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify power supply voltage is within specifications.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "e9": {
        "name": ".1].",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm e9 - .1].: .1].</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "f0": {
        "name": "Tough drive warning]) are not recorded in the alarm",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm f0 - Tough drive warning]) are not recorded in the alarm: history. • [AL. 8D.1 CC-Link IE communication error 1] and [AL.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "f3": {
        "name": "]) do not have alarm codes. The alarm codes in the following",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm f3 - ]) do not have alarm codes. The alarm codes in the following: table will be outputted when they occur.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "f4": {
        "name": ".6].",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm f4 - .6].: .6].</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "0.1": {
        "name": "Excessive regeneration warning  Common ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 0.1 - Excessive regeneration warning  Common : Alarm 0.1: Excessive regeneration warning  Common </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "0.2": {
        "name": "s or less.)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 0.2 - s or less.): Check if the motor was accelerated suddenly to r/ min by an external force.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Verify power supply voltage is within specifications.</li>
    </ol>
  </div>
</div>"""
    },
    "0.3": {
        "name": "Vibration tough drive warning  Each axis ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 0.3 - Vibration tough drive warning  Each axis : F2 Drive recorder - Miswriting warning F</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "0.5": {
        "name": "pulses hold by the Simple Motion module/Motion",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 0.5 - pulses hold by the Simple Motion module/Motion: module is cleared to 0 at start and not carried to next positioning.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "1.0": {
        "name": "[m] and movement for 2.5 [m] is executed two times.",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 1.0 - [m] and movement for 2.5 [m] is executed two times.:  Conversion to command pulses: 2.5 [m]/1.0 = 2.5 [pulse] When the \\"reference axis speed\\" is set in 2- to 4-axis fixed-feed control, set so the major axis side becomes the reference axis.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "1.8": {
        "name": "Thermal overload error 4 during a stop  Each axis ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 1.8 - Thermal overload error 4 during a stop  Each axis : E2 Servo motor overheat warning E</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "2.5": {
        "name": "[m]/1.0 = 2.5 [pulse]",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 2.5 - [m]/1.0 = 2.5 [pulse]: When the \\"reference axis speed\\" is set in 2- to 4-axis fixed-feed control, set so the major axis side becomes the reference axis.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "2.8": {
        "name": "[Pr. PT34] of",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 2.8 - [Pr. PT34] of: J4-_A_-RJ Servo Amplifier Instruction Manual (Positioning Mode)\\") [A] It was changed by mistake.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "2.9": {
        "name": "[Pr.",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 2.9 - [Pr.: PT34] of \\"MR-J4-_A_- RJ Servo Amplifier Instruction Manual (Positioning Mode)\\" MR-J4-_GF_(-RJ) Servo Amplifier Instruction Manual (I/O Mode) • Section 7.2.4 [Pr.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "3.0": {
        "name": "V DC. Replace the battery.",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 3.0 - V DC. Replace the battery.: It is 3.0 V DC or more. Check (2).</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>If issue persists, replace battery, then check the repeatability.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "3.2": {
        "name": "V or less.",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 3.2 - V or less.: [Operation status at warning occurrence] The synchronous encoder control continues.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>If issue persists, replace battery.</li>
      <li>Inspect encoder connections and verify encoder operation.</li>
    </ol>
  </div>
</div>"""
    },
    "3.5": {
        "name": "Encoder absolute positioning counter",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 3.5 - Encoder absolute positioning counter: warning   E4 Parameter warning E</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "4.6": {
        "name": "Acceleration time constant setting range",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 4.6 - Acceleration time constant setting range: error warning  F</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "4.7": {
        "name": "Deceleration time constant setting range",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 4.7 - Deceleration time constant setting range: error warning  F</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "4.9": {
        "name": "Home position return type error warning ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 4.9 - Home position return type error warning : Warning Detail</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "5.7": {
        "name": "(2) of",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 5.7 - (2) of: \\"MR-J4-_GF_(-RJ) SERVO AMPLIFIER INSTRUCTION MANUAL (CC-Link IE Field Network Basic)\\" Or set a larger setting value to \\"in-position range\\".</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "6.3": {
        "name": "SS1 forced stop warning 2 (safety",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 6.3 - SS1 forced stop warning 2 (safety: observation function) SD  E7 Controller forced stop warning E</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "6.4": {
        "name": "Cam control data setting range error ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 6.4 - Cam control data setting range error : Cam control data setting range error </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "6.5": {
        "name": "Cam No. external error ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 6.5 - Cam No. external error : Cam No. external error </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "6.6": {
        "name": "Cam control inactive ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 6.6 - Cam control inactive : F7 Machine diagnosis warning F</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "9.2": {
        "name": "Bus voltage drop during low speed",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 9.2 - Bus voltage drop during low speed: operation E</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "9.3": {
        "name": "Ready-on signal on during main circuit off DB Common All axes",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 9.3 - Ready-on signal on during main circuit off DB Common All axes: Ready-on signal on during main circuit off DB Common All axes</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "9.4": {
        "name": "Converter unit forced stop DB ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 9.4 - Converter unit forced stop DB : EA ABS servo-on warning EA.1 ABS servo-on warning  EB The other axis error warning EB.1 The other axis error warning EC Overload warning 2 EC.1.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "12.1": {
        "name": "Precautions for Creating Program",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 12.1 - Precautions for Creating Program: 12 PROGRAMMING [FX5-SSC-S] This chapter describes the programs required to carry out positioning control with the Simple Motion module.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "12.2": {
        "name": "Creating a Program 619",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 12.2 - Creating a Program 619: Creating a Program 619</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "12.3": {
        "name": "Positioning Program Examples (For Using Labels)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 12.3 - Positioning Program Examples (For Using Labels): Positioning Program Examples (For Using Labels)</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "12.4": {
        "name": "Positioning Program Examples (For Using Buffer Memory)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 12.4 - Positioning Program Examples (For Using Buffer Memory): Positioning Program Examples (For Using Buffer Memory)</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "12.5": {
        "name": "RAM error 5 DB   Common All axes",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 12.5 - RAM error 5 DB   Common All axes: 12.6 RAM error 6     13 Clock error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "12.6": {
        "name": "RAM error 6 DB    ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 12.6 - RAM error 6 DB    : 13 Clock error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "13.1": {
        "name": "Precautions for Creating Program",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 13.1 - Precautions for Creating Program: 13 PROGRAMMING [FX5-SSC-G] This chapter describes the programs required to carry out positioning control with the Motion module.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "13.2": {
        "name": "Creating a Program 671",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 13.2 - Creating a Program 671: Creating a Program 671</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "13.3": {
        "name": "Positioning Program Examples (For Using Labels)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 13.3 - Positioning Program Examples (For Using Labels): Positioning Program Examples (For Using Labels)</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "14.1": {
        "name": "Troubleshooting Procedure 715",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 14.1 - Troubleshooting Procedure 715: 14 14 TROUBLESHOOTING This chapter describes details of error occurred by using the Simple Motion module/Motion module and troubleshooting</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "14.2": {
        "name": "Troubleshooting by Symptom",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 14.2 - Troubleshooting by Symptom: Troubleshooting by Symptom</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "14.3": {
        "name": "Error and Warning Details",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 14.3 - Error and Warning Details: Error and Warning Details</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "14.4": {
        "name": "List of Warning Codes 727",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 14.4 - List of Warning Codes 727: List of Warning Codes 727</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "14.5": {
        "name": "List of Error Codes 749",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 14.5 - List of Error Codes 749: List of Error Codes 749</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "14.6": {
        "name": "Control process",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 14.6 - Control process: error 6  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "14.7": {
        "name": "Control process",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 14.7 - Control process: error 7  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "14.8": {
        "name": "Control process",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 14.8 - Control process: error 8  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "14.9": {
        "name": "Control process",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 14.9 - Control process: error 9  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "15.1": {
        "name": "EEP-ROM error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 15.1 - EEP-ROM error: at power on   C o m m o n A l l a x e s 15.2 EEP-ROM error during operation  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify power supply voltage is within specifications.</li>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "15.2": {
        "name": "EEP-ROM error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 15.2 - EEP-ROM error: during operation  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "15.4": {
        "name": "Home position",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 15.4 - Home position: information read error    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "16.1": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 16.1 - Encoder initial: communication - Receive data error 1  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "16.2": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 16.2 - Encoder initial: communication - Receive data error 2  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "16.3": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 16.3 - Encoder initial: communication - Receive data error 3  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "16.4": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 16.4 - Encoder initial: communication - Encoder malfunction  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "16.5": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 16.5 - Encoder initial: communication - Transmission data error 1  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "16.6": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 16.6 - Encoder initial: communication - Transmission data error 2  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "16.7": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 16.7 - Encoder initial: communication - Transmission data error 3  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "16.8": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 16.8 - Encoder initial: communication - Incompatible encoder  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "17.1": {
        "name": "Board error 1 DB   C o m m o n A l l  a x e s 0000",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 17.1 - Board error 1 DB   C o m m o n A l l  a x e s 0000: Board error 1 DB   C o m m o n A l l  a x e s 0000</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "17.3": {
        "name": "Board error 2 DB   Common All axes",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 17.3 - Board error 2 DB   Common All axes: Board error 2 DB   Common All axes</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "17.4": {
        "name": "Board error 3 DB   Common All axes",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 17.4 - Board error 3 DB   Common All axes: Board error 3 DB   Common All axes</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "17.5": {
        "name": "Board error 4 DB   Common All axes",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 17.5 - Board error 4 DB   Common All axes: Board error 4 DB   Common All axes</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "17.6": {
        "name": "Board error 5 DB   Common All axes",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 17.6 - Board error 5 DB   Common All axes: Board error 5 DB   Common All axes</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "17.7": {
        "name": "Board error 7 DB    ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 17.7 - Board error 7 DB    : Board error 7 DB    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "17.8": {
        "name": "Board error 6 *6 EDB   Common All axes",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 17.8 - Board error 6 *6 EDB   Common All axes: Board error 6 *6 EDB   Common All axes</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "17.9": {
        "name": "Board error 8 DB    ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 17.9 - Board error 8 DB    : 19 Memory error 3 (Flash-ROM)</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "19.1": {
        "name": "Flash-ROM",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 19.1 - Flash-ROM: error 1   C o m m o n A l l a x e s</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "19.2": {
        "name": "Flash-ROM",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 19.2 - Flash-ROM: error 2  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "19.3": {
        "name": "Flash-ROM",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 19.3 - Flash-ROM: error 3     1A Servo motor combination error 1A.1 Servo motor combination error 1   1A.2 Servo motor control mode combination error  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "20.1": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 20.1 - Encoder normal: communication - Receive data error 1 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "20.2": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 20.2 - Encoder normal: communication - Receive data error 2 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "20.3": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 20.3 - Encoder normal: communication - Receive data error 3 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "20.5": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 20.5 - Encoder normal: communication - Transmission data error 1 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "20.6": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 20.6 - Encoder normal: communication - Transmission data error 2 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "20.7": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 20.7 - Encoder normal: communication - Transmission data error 3 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "20.9": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 20.9 - Encoder normal: communication - Receive data error 4 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "21.1": {
        "name": "Encoder data",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 21.1 - Encoder data: error 1 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "21.2": {
        "name": "Encoder data",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 21.2 - Encoder data: update error E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "21.3": {
        "name": "Encoder data",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 21.3 - Encoder data: waveform error E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "21.4": {
        "name": "Encoder non-",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 21.4 - Encoder non-: signal error E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "21.5": {
        "name": "Encoder",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 21.5 - Encoder: hardware error 1 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "21.6": {
        "name": "Encoder",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 21.6 - Encoder: hardware error 2 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "21.9": {
        "name": "Encoder data",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 21.9 - Encoder data: error 2 E   24 Main circuit error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "24.1": {
        "name": "Ground fault",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 24.1 - Ground fault: detected by hardware detection circuit   E a c h a x i s A l l a x e s</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "24.2": {
        "name": "Ground fault",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 24.2 - Ground fault: detected by software detection function   All axes</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "25.1": {
        "name": "Servo motor",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 25.1 - Servo motor: encoder - Absolute position erased  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "25.2": {
        "name": "Scale",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 25.2 - Scale: measurement encoder - Absolute position erased   27 Initial magnetic pole detection error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "25.4": {
        "name": "= mm setting",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 25.4 - = mm setting: value. If interpolation control units are \\"inch\\", positioning is contro lled by calculating position commands from the address, travel value,.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "27.1": {
        "name": "Initial magnetic",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 27.1 - Initial magnetic: pole detection - Abnormal termination  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "27.2": {
        "name": "Initial magnetic",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 27.2 - Initial magnetic: pole detection - Time out error  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "27.3": {
        "name": "Initial magnetic",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 27.3 - Initial magnetic: pole detection - Limit switch error  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "27.4": {
        "name": "Initial magnetic",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 27.4 - Initial magnetic: pole detection - Estimated error  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "27.5": {
        "name": "Initial magnetic",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 27.5 - Initial magnetic: pole detection - Speed deviation error  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "27.6": {
        "name": "Initial magnetic",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 27.6 - Initial magnetic: pole detection - Position deviation error  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "27.7": {
        "name": "Initial magnetic",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 27.7 - Initial magnetic: pole detection - Current error   28 Linear encoder error 2</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "28.1": {
        "name": "Linear encoder -",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 28.1 - Linear encoder -: Environment error E   2A Linear encoder error 1 2A.1 Linear encoder error 1-1 E   2A.2 Linear encoder error 1-2 E   Eac</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "29.0": {
        "name": "(Device input polarity 1): 1h: Dog detection",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 29.0 - (Device input polarity 1): 1h: Dog detection: 1h: Dog detection: with on [Operation status at error occurrence] Current value restoration is not performed for the relevant servo amplifier.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "30.1": {
        "name": "Regeneration",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 30.1 - Regeneration: heat error    C o m m o n A l l a x e s</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "30.2": {
        "name": "Regeneration",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 30.2 - Regeneration: signal error   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "30.3": {
        "name": "Regeneration",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 30.3 - Regeneration: feedback signal error    31 Overspeed</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "31.1": {
        "name": "Abnormal motor",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 31.1 - Abnormal motor: speed SD   32 Overcurrent</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "32.1": {
        "name": "Overcurrent",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 32.1 - Overcurrent: detected at hardware detection circuit (during operation)   E a c h a x i s A l l a x e s</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "32.2": {
        "name": "Overcurrent",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 32.2 - Overcurrent: detected at software detection function (during operation)   All axes</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "32.3": {
        "name": "Overcurrent",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 32.3 - Overcurrent: detected at hardware detection circuit (during a stop)   All axes</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "32.4": {
        "name": "Overcurrent",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 32.4 - Overcurrent: detected at software detection function (during a stop)   All axes 33 Overvoltage</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify power supply voltage is within specifications.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "33.1": {
        "name": "Main circuit",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 33.1 - Main circuit: voltage error E   C o m m o n A l l a x e s 34 SSCNET receive error 1 34.1 SSCNET receive data error SD    34.2 SSCNET connector connection.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify power supply voltage is within specifications.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "34.1": {
        "name": "SSCNET",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 34.1 - SSCNET: receive data error SD    34.2 SSCNET connector connection error SD    34.3 SSCNET communication data error SD  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "34.2": {
        "name": "SSCNET",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 34.2 - SSCNET: connector connection error SD    34.3 SSCNET communication data error SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "34.3": {
        "name": "SSCNET",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 34.3 - SSCNET: communication data error SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "34.4": {
        "name": "Hardware error",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 34.4 - Hardware error: signal detection SD    34.5 SSCNET receive data error (safety observation function) SD     34.6 SSCNET communication data error.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "34.5": {
        "name": "SSCNET",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 34.5 - SSCNET: receive data error (safety observation function) SD     34.6 SSCNET communication data error (safety observation function) SD    .</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "34.6": {
        "name": "SSCNET",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 34.6 - SSCNET: communication data error (safety observation function) SD     35 Command frequency error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "35.1": {
        "name": "Command",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 35.1 - Command: frequency error SD  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "36.1": {
        "name": "Continuous",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 36.1 - Continuous: communication data error SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "36.2": {
        "name": "Continuous",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 36.2 - Continuous: communication data error (safety observation function) SD     37 Parameter error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "37.1": {
        "name": "Parameter",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 37.1 - Parameter: setting range error  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "37.2": {
        "name": "Parameter",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 37.2 - Parameter: combination error  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "37.3": {
        "name": "Point table",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 37.3 - Point table: setting error     39 Program error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "39.1": {
        "name": "Program error DB     0000",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 39.1 - Program error DB     0000: Program error DB     0000</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "39.2": {
        "name": "Instruction",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 39.2 - Instruction: argument external error    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "39.3": {
        "name": "Register No.",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 39.3 - Register No.: error    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "39.4": {
        "name": "Non-",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 39.4 - Non-: correspondence instruction error     3A Inrush current suppression circuit error 3A.1 Inrush current suppression circuit error E   C o m m o.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "41.2": {
        "name": "(Limit switch enabled status selection): 1h",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 41.2 - (Limit switch enabled status selection): 1h: 1h: • PD41.3 (Sensor input method selection): 1h (Input from controller (FLS/RLS/DOG)) • PD60 (DI pin polarity selection): 00000000h • PT01.1.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "41.3": {
        "name": "(Sensor input method selection): 1h (Input",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 41.3 - (Sensor input method selection): 1h (Input: 1h (Input: from controller (FLS/RLS/DOG)) • PD60 (DI pin polarity selection): 00000000h • PT01.1 (Speed/acceleration/deceleration unit selection): 0h.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "42.1": {
        "name": "Servo control",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 42.1 - Servo control: error by position deviation E </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "42.2": {
        "name": "Servo control",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 42.2 - Servo control: error by speed deviation E </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "42.3": {
        "name": "Servo control",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 42.3 - Servo control: error by torque/ thrust deviation E  Fully closed loop control error (for fully closed loop control)</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "42.8": {
        "name": "Fully closed",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 42.8 - Fully closed: loop control error by position deviation E </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "42.9": {
        "name": "Fully closed",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 42.9 - Fully closed: loop control error by speed deviation E </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "45.1": {
        "name": "Main circuit",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 45.1 - Main circuit: device overheat error 1 SD    C o m m o n A l l a x e s</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "45.2": {
        "name": "Main circuit",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 45.2 - Main circuit: device overheat error 2 SD    46 Servo motor overheat</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "46.1": {
        "name": "Abnormal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 46.1 - Abnormal: temperature of servo motor 1 SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
    </ol>
  </div>
</div>"""
    },
    "46.2": {
        "name": "Abnormal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 46.2 - Abnormal: temperature of servo motor 2 SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
    </ol>
  </div>
</div>"""
    },
    "46.3": {
        "name": "Thermistor",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 46.3 - Thermistor: disconnected error SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
    </ol>
  </div>
</div>"""
    },
    "46.4": {
        "name": "Thermistor",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 46.4 - Thermistor: circuit error SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "46.5": {
        "name": "Abnormal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 46.5 - Abnormal: temperature of servo motor 3   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "46.6": {
        "name": "Abnormal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 46.6 - Abnormal: temperature of servo motor 4    47 Cooling fan error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "47.1": {
        "name": "Cooling fan stop",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 47.1 - Cooling fan stop: error SD   C o m m o n A l l a x e s</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "47.2": {
        "name": "Cooling fan",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 47.2 - Cooling fan: speed reduction error SD  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "50.1": {
        "name": "Thermal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 50.1 - Thermal: overload error 1 during operation SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "50.2": {
        "name": "Thermal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 50.2 - Thermal: overload error 2 during operation SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "50.3": {
        "name": "Thermal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 50.3 - Thermal: overload error 4 during operation SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "50.4": {
        "name": "Thermal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 50.4 - Thermal: overload error 1 during a stop SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "50.5": {
        "name": "Thermal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 50.5 - Thermal: overload error 2 during a stop SD   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "50.6": {
        "name": "Thermal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 50.6 - Thermal: overload error 4 during a stop SD    51 Overload 2</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "51.1": {
        "name": "Thermal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 51.1 - Thermal: overload error 3 during operation   </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "51.2": {
        "name": "Thermal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 51.2 - Thermal: overload error 3 during a stop    52 Error excessive</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "52.1": {
        "name": "Excess droop",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 52.1 - Excess droop: pulse 1 SD  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "52.3": {
        "name": "Excess droop",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 52.3 - Excess droop: pulse 2 SD  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "52.4": {
        "name": "Error excessive",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 52.4 - Error excessive: during 0 torque limit SD  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "52.5": {
        "name": "Excess droop",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 52.5 - Excess droop: pulse 3 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "52.6": {
        "name": "Excess droop",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 52.6 - Excess droop: pulse during servo-off SD   54 Oscillation detection</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "54.1": {
        "name": "Oscillation",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 54.1 - Oscillation: detection error E   56 Forced stop error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "56.2": {
        "name": "Over speed",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 56.2 - Over speed: during forced stop E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "56.3": {
        "name": "Estimated",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 56.3 - Estimated: distance over during forced stop E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "56.4": {
        "name": "Forced stop",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 56.4 - Forced stop: start error E   61 Operation error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "61.1": {
        "name": "Point table",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 61.1 - Point table: setting range error     63 STO timing error 63.1 STO1 off   C o m m o n A l l a x e s 63.2 STO2 off   63.5 STO by functional safety unit.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "63.1": {
        "name": "STO1 off DB   C o m m o n A l l  a x e s 0110",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 63.1 - STO1 off DB   C o m m o n A l l  a x e s 0110: 63.2 STO2 off   63.5 STO by functional safety unit    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "63.2": {
        "name": "STO2 off DB   Common All axes",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 63.2 - STO2 off DB   Common All axes: 63.5 STO by functional safety unit    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "63.5": {
        "name": "STO by",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 63.5 - STO by: functional safety unit    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "64.1": {
        "name": "STO input error DB     1000",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 64.1 - STO input error DB     1000: STO input error DB     1000</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "64.2": {
        "name": "Compatibility",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 64.2 - Compatibility: mode setting error    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "64.3": {
        "name": "Operation mode",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 64.3 - Operation mode: setting error     65 Functional safety unit connection error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "65.1": {
        "name": "Functional",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 65.1 - Functional: safety unit communication error 1 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "65.2": {
        "name": "Functional",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 65.2 - Functional: safety unit communication error 2 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "65.3": {
        "name": "Functional",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 65.3 - Functional: safety unit communication error 3 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "65.4": {
        "name": "Functional",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 65.4 - Functional: safety unit communication error 4 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "65.5": {
        "name": "Functional",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 65.5 - Functional: safety unit communication error 5 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "65.6": {
        "name": "Functional",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 65.6 - Functional: safety unit communication error 6 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "65.7": {
        "name": "Functional",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 65.7 - Functional: safety unit communication error 7 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "65.8": {
        "name": "Functional",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 65.8 - Functional: safety unit shut- off signal error 1    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "65.9": {
        "name": "Functional",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 65.9 - Functional: safety unit shut- off signal error 2    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "66.1": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 66.1 - Encoder initial: communication - Receive data error 1 (safety observation function)    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "66.2": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 66.2 - Encoder initial: communication - Receive data error 2 (safety observation function)    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "66.3": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 66.3 - Encoder initial: communication - Receive data error 3 (safety observation function)    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "66.7": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 66.7 - Encoder initial: communication - Transmission data error 1 (safety observation function)    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "66.9": {
        "name": "Encoder initial",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 66.9 - Encoder initial: communication - Process error 1 (safety observation function)     67 Encoder normal communication error 1 (safety observation function)</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "67.1": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 67.1 - Encoder normal: communication - Receive data error 1 (safety observation function)    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "67.2": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 67.2 - Encoder normal: communication - Receive data error 2 (safety observation function)    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "67.3": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 67.3 - Encoder normal: communication - Receive data error 3 (safety observation function)    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "67.4": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 67.4 - Encoder normal: communication - Receive data error 4 (safety observation function)    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "67.5": {
        "name": "33.75",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 67.5 - 33.75: When unit setting is other than the above 675</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "67.7": {
        "name": "Encoder normal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 67.7 - Encoder normal: communication - Transmission data error 1 (safety observation function)     68 STO diagnosis error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "68.1": {
        "name": "Mismatched",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 68.1 - Mismatched: STO signal error   C o m m o n C o m m o n</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "69.1": {
        "name": "Forward",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 69.1 - Forward: rotation-side software limit detection - Command excess error SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "69.2": {
        "name": "Reverse",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 69.2 - Reverse: rotation-side software limit detection - Command excess error SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "69.3": {
        "name": "Forward rotation",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 69.3 - Forward rotation: stroke end detection - Command excess error SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "69.4": {
        "name": "Reverse",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 69.4 - Reverse: rotation stroke end detection - Command excess error SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "69.5": {
        "name": "Upper stroke",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 69.5 - Upper stroke: limit detection - Command excess error SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "69.6": {
        "name": "Lower stroke",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 69.6 - Lower stroke: limit detection - Command excess error SD     70 Load-side encoder initial communication error 1</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "70.1": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 70.1 - Load-side: encoder initial communication - Receive data error 1  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "70.2": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 70.2 - Load-side: encoder initial communication - Receive data error 2  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "70.3": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 70.3 - Load-side: encoder initial communication - Receive data error 3  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "70.4": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 70.4 - Load-side: encoder initial communication - Encoder malfunction  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "70.5": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 70.5 - Load-side: encoder initial communication - Transmission data error 1  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "70.6": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 70.6 - Load-side: encoder initial communication - Transmission data error 2  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "70.7": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 70.7 - Load-side: encoder initial communication - Transmission data error 3  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "70.8": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 70.8 - Load-side: encoder initial communication - Incompatible encoder  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "71.1": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 71.1 - Load-side: encoder normal communication - Receive data error 1 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "71.2": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 71.2 - Load-side: encoder normal communication - Receive data error 2 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "71.3": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 71.3 - Load-side: encoder normal communication - Receive data error 3 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "71.5": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 71.5 - Load-side: encoder normal communication - Transmission data error 1 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "71.6": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 71.6 - Load-side: encoder normal communication - Transmission data error 2 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "71.7": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 71.7 - Load-side: encoder normal communication - Transmission data error 3 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "71.9": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 71.9 - Load-side: encoder normal communication - Receive data error 4 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "72.1": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 72.1 - Load-side: encoder data error 1 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "72.2": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 72.2 - Load-side: encoder data update error E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "72.3": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 72.3 - Load-side: encoder data waveform error E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "72.4": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 72.4 - Load-side: encoder non- signal error E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "72.5": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 72.5 - Load-side: encoder hardware error 1 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "72.6": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 72.6 - Load-side: encoder hardware error 2 E  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "72.9": {
        "name": "Load-side",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 72.9 - Load-side: encoder data error 2 E   74 Option card error 1</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "74.1": {
        "name": "Option card",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 74.1 - Option card: error 1    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "74.2": {
        "name": "Option card",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 74.2 - Option card: error 2    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "74.3": {
        "name": "Option card",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 74.3 - Option card: error 3    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "74.4": {
        "name": "Option card",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 74.4 - Option card: error 4    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
    </ol>
  </div>
</div>"""
    },
    "74.5": {
        "name": "Option card",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 74.5 - Option card: error 5     75 Option card error 2</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
    </ol>
  </div>
</div>"""
    },
    "75.3": {
        "name": "Option card",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 75.3 - Option card: connection error E    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
    </ol>
  </div>
</div>"""
    },
    "75.4": {
        "name": "Option card",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 75.4 - Option card: disconnected    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
      <li>Verify power supply voltage is within specifications.</li>
    </ol>
  </div>
</div>"""
    },
    "79.0": {
        "name": "(DI status read selection): Eh",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 79.0 - (DI status read selection): Eh: Eh: • PD41.2 (Limit switch enabled status selection): 1h • PD41.3 (Sensor input method selection): 1h (Input from controller (FLS/RLS/DOG)) • PD60.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "79.1": {
        "name": "Functional",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 79.1 - Functional: safety unit power voltage error    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify power supply voltage is within specifications.</li>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
    </ol>
  </div>
</div>"""
    },
    "79.2": {
        "name": "Functional",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 79.2 - Functional: safety unit internal error    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
    </ol>
  </div>
</div>"""
    },
    "79.3": {
        "name": "Abnormal",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 79.3 - Abnormal: temperature of functional safety unit SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check the servo amplifier for faults.</li>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
    </ol>
  </div>
</div>"""
    },
    "79.4": {
        "name": "Servo amplifier",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 79.4 - Servo amplifier: error SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Disconnect cables except control circuit power supply and check repeatability.</li>
      <li>If repeatable, replace the servo amplifier.</li>
      <li>If not repeatable, check surrounding environment (noise, temperature).</li>
    </ol>
  </div>
</div>"""
    },
    "79.5": {
        "name": "Input device",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 79.5 - Input device: error SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "79.6": {
        "name": "Output device",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 79.6 - Output device: error SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "79.7": {
        "name": "Mismatched",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 79.7 - Mismatched: input signal error SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "79.8": {
        "name": "Position",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 79.8 - Position: feedback fixing error     7A Parameter setting error (safety observation function) 7A.1 Parameter verification error (safety observation.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "82.1": {
        "name": "Master-slave",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 82.1 - Master-slave: operation error 1 E     84 Network module initialization error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "84.1": {
        "name": "Network module",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 84.1 - Network module: undetected error    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "84.2": {
        "name": "Network module",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 84.2 - Network module: initialization error 1    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "84.3": {
        "name": "Network module",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 84.3 - Network module: initialization error 2     85 Network module error</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "85.1": {
        "name": "Network module",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 85.1 - Network module: error 1 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "85.2": {
        "name": "Network module",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 85.2 - Network module: error 2 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "85.3": {
        "name": "Network module",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 85.3 - Network module: error 3 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify power supply voltage is within specifications.</li>
      <li>Check all communication cables and connectors.</li>
      <li>Verify network module is properly seated.</li>
      <li>Check communication parameter settings match the controller.</li>
    </ol>
  </div>
</div>"""
    },
    "86.1": {
        "name": "Network",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 86.1 - Network: communication error 1 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "86.2": {
        "name": "Network",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 86.2 - Network: communication error 2 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "86.3": {
        "name": "Network",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 86.3 - Network: communication error 3 SD    </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "86.4": {
        "name": "Network",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 86.4 - Network: communication error 4 SD     8A USB communication time-out error/ serial communication time-out error/ Modbus RTU communication time-out.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "90.1": {
        "name": "Home position return incomplete ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 90.1 - Home position return incomplete : Home position return incomplete </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
      <li>Check the servo amplifier for faults.</li>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
    </ol>
  </div>
</div>"""
    },
    "90.2": {
        "name": "Home position return abnormal termination ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 90.2 - Home position return abnormal termination : 90.5 Z-phase unpassed  91 Servo amplifier overheat warning</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
      <li>Check the servo amplifier for faults.</li>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
    </ol>
  </div>
</div>"""
    },
    "90.5": {
        "name": "Z-phase unpassed ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 90.5 - Z-phase unpassed : 91 Servo amplifier overheat warning</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
      <li>Check the servo amplifier for faults.</li>
      <li>Inspect encoder connections and verify encoder operation.</li>
      <li>Check ambient temperature and ensure adequate ventilation.</li>
    </ol>
  </div>
</div>"""
    },
    "91.1": {
        "name": "Main circuit device overheat warning  Common ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 91.1 - Main circuit device overheat warning  Common : 92 Battery cable disconnection warning</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check all cable connections for damage or loose contacts.</li>
      <li>Disconnect and reconnect cables to ensure proper seating.</li>
      <li>Inspect encoder connections and verify encoder operation.</li>
    </ol>
  </div>
</div>"""
    },
    "92.1": {
        "name": "Encoder battery cable disconnection",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 92.1 - Encoder battery cable disconnection: warning  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Check encoder cable connections at both ends.</li>
      <li>Inspect encoder cable for damage or wear.</li>
      <li>If issue persists after cable check, replace the encoder.</li>
    </ol>
  </div>
</div>"""
    },
    "92.3": {
        "name": "Battery degradation  Each axis ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 92.3 - Battery degradation  Each axis : 93 ABS data transfer warning 93.1 ABS data transfer requirement warning during magnetic pole detection  95 STO warning 95.1 STO1 off detection.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "93.1": {
        "name": "ABS data transfer requirement warning",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 93.1 - ABS data transfer requirement warning: during magnetic pole detection  95 STO warning 95.1 STO1 off detection 95.2 STO2 off detection 95.3 STO warning 1 (safety observation function) .</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "95.1": {
        "name": "STO1 off detection DB Common All axes",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 95.1 - STO1 off detection DB Common All axes: 95.2 STO2 off detection 95.3 STO warning 1 (safety observation function)  95.4 STO warning 2 (safety observation function)  95.5 STO warning 3.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "95.2": {
        "name": "STO2 off detection DB Common All axes",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 95.2 - STO2 off detection DB Common All axes: 95.3 STO warning 1 (safety observation function)  95.4 STO warning 2 (safety observation function)  95.5 STO warning 3 (safety observation.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "95.3": {
        "name": "STO warning 1 (safety observation function) DB ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 95.3 - STO warning 1 (safety observation function) DB : 95.4 STO warning 2 (safety observation function)  95.5 STO warning 3 (safety observation function)  96 Home position setting warning</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "95.4": {
        "name": "STO warning 2 (safety observation function) DB ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 95.4 - STO warning 2 (safety observation function) DB : 95.5 STO warning 3 (safety observation function)  96 Home position setting warning</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "95.5": {
        "name": "STO warning 3 (safety observation function) DB ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 95.5 - STO warning 3 (safety observation function) DB : 96 Home position setting warning</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "96.1": {
        "name": "In-position warning at home positioning  Each axis ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 96.1 - In-position warning at home positioning  Each axis : In-position warning at home positioning  Each axis </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "96.2": {
        "name": "Command input warning at home",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 96.2 - Command input warning at home: positioning  </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "96.3": {
        "name": "Servo off warning at home positioning ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 96.3 - Servo off warning at home positioning : Servo off warning at home positioning </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "96.4": {
        "name": "Home positioning warning during magnetic",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 96.4 - Home positioning warning during magnetic: pole detection  97 Positioning specification warning</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "97.1": {
        "name": "Program operation disabled warning ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 97.1 - Program operation disabled warning : Program operation disabled warning </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "97.2": {
        "name": "Next station position warning ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 97.2 - Next station position warning : 98 Software limit warning</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "98.1": {
        "name": "Forward rotation-side software stroke limit",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 98.1 - Forward rotation-side software stroke limit: reached </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "98.2": {
        "name": "Reverse rotation-side software stroke limit",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 98.2 - Reverse rotation-side software stroke limit: reached  99 Stroke limit warning</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "99.1": {
        "name": "Forward rotation stroke end off *4*7 ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 99.1 - Forward rotation stroke end off *4*7 : Forward rotation stroke end off *4*7 </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "99.2": {
        "name": "Reverse rotation stroke end off *4*7 ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 99.2 - Reverse rotation stroke end off *4*7 : Reverse rotation stroke end off *4*7 </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "99.4": {
        "name": "Upper stroke limit off *7 Each axis ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 99.4 - Upper stroke limit off *7 Each axis : Upper stroke limit off *7 Each axis </p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "99.5": {
        "name": "Lower stroke limit off *7 Each axis ",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 99.5 - Lower stroke limit off *7 Each axis : 9A Optional unit input data error warning 9A.1 Optional unit input data sign error  9A.2 Optional unit BCD input data error  9B Error excessive.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "2.000": {
        "name": "0.4 to 2.8 0 to 2.0 0 to 2.0 6.0 to 6.4 0 to 2.0 Follows",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 2.000 - 0.4 to 2.8 0 to 2.0 0 to 2.0 6.0 to 6.4 0 to 2.0 Follows: parameters 4.000 0.4 to 4.5 0 to 4.0 0 to 4.0 12.0 to 12.2 0 to</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "337.5": {
        "name": "Error code",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 337.5 - Error code: (Hexadecimal) [FX5-SSC-S] Error name Error details and causes Remedy 3022H System bus error Communication with CPU module did not complete properly.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Verify network/communication cable connections.</li>
      <li>Check for communication parameter settings.</li>
    </ol>
  </div>
</div>"""
    },
    "4.000": {
        "name": "0.4 to 4.5 0 to 4.0 0 to 4.0 12.0 to 12.2 0 to 4.0 Follows",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 4.000 - 0.4 to 4.5 0 to 4.0 0 to 4.0 12.0 to 12.2 0 to 4.0 Follows: parameters Standby Position control Standby t1 t2 t3 t4 t5 t2 t6 [Cd.184] Positioning start [Md.141] BUSY Positioning complete signal ([Md.31].</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "562.5": {
        "name": "When unit is set to degree and",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 562.5 - When unit is set to degree and: multiplier setting for degree axis\\" is valid 67.5</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "88888": {
        "name": "Watchdog",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 88888 - Watchdog:  [RJ010]: MR-J3-T10 came off.  A part such as CPU is malfunctioning</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "3076.7": {
        "name": "r/min",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 3076.7 - r/min: • When CMX > , N < .7 - (CMX × 0.1) r/min • When (CMX/CDV) is reduced to its lowest terms, CMX  15900 The operation was out of conditions.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "3276.7": {
        "name": "- (CMX × 0.1)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 3276.7 - - (CMX × 0.1): r/min • When (CMX/CDV) is reduced to its lowest terms, CMX  15900 The operation was out of conditions.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "5000.0": {
        "name": "m",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 5000.0 - m: • Set the following data. (Set using the program referring to the start time chart.) n: Axis No.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "3000.00": {
        "name": "mm/min (Speed is limited at a ratio of an axis 1 command speed to an axis 2 command speed.)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 3000.00 - mm/min (Speed is limited at a ratio of an axis 1 command speed to an axis 2 command speed.): Operation runs at speed 1 when a reference axis speed is less than 1 as a result of speed limit.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "31500.0": {
        "name": "READY signal READY",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 31500.0 - READY signal READY: U1\\G</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "31500.1": {
        "name": "Synchronization flag Buffer memory accessible",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 31500.1 - Synchronization flag Buffer memory accessible: U1\\G2417.C  M code ON signal M code outputting U1\\G</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "31501.0": {
        "name": "BUSY signal BUSY (operating)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 31501.0 - BUSY signal BUSY (operating): U1\\G</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "4000.00": {
        "name": "mm/min (Speed is limited by [Pr.8].)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 4000.00 - mm/min (Speed is limited by [Pr.8].): • Axis 2: .00 mm/min (Speed is limited at a ratio of an axis 1 command speed to an axis 2 command speed.) Operation runs at speed 1 when a reference.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "631500.0": {
        "name": "READY signal READY",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 631500.0 - READY signal READY: address of U1\\</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "631500.1": {
        "name": "Synchronization flag Buffer memory accessible",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 631500.1 - Synchronization flag Buffer memory accessible: Simple Motion module U1\\62417.C | — M code ON signal M code outputting U1\\</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier.</li>
      <li>If alarm recurs, the internal memory may be corrupted.</li>
      <li>Replace the servo amplifier if the error persists.</li>
    </ol>
  </div>
</div>"""
    },
    "631501.0": {
        "name": "BUSY signal BUSY (operating)",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 631501.0 - BUSY signal BUSY (operating): U1\\G</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "270.00000": {
        "name": "[degree])",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 270.00000 - [degree]): t V [Cd.184] Positioning start OFF ON [Da.8] Command speed [Md.141] BUSY OFF ON Positioning complete signal ([Md.31] Status: b15) OFF ON.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "359.99999": {
        "name": "[degree]).",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 359.99999 - [degree]).: [Operation status at warning occurrence] The target position change is not carried out.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
    "360.00000": {
        "name": "or less or",
        "content": """<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>Alarm 360.00000 - or less or: 360.00000 or more using INC instruction, where the control unit is set to \\"degree\\" and \\"[Pr.12] Software stroke limit upper limit value\\" is.</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>Cycle power to the servo amplifier and check if alarm clears.</li>
      <li>If alarm persists, check related components and wiring.</li>
      <li>Consult the servo manual for detailed diagnostics.</li>
    </ol>
  </div>
</div>"""
    },
}

def classify_query(query: str) -> str:
    """Classify query type for better prompt selection."""
    query_lower = query.lower()
    
    # Servo alarm/error pattern - more specific detection
    if re.search(r'\b(alarm|error|fault|code)\s*[a-z]?\d+\.?\d*\b', query_lower, re.IGNORECASE):
        return "error_code"
    
    # Detect "what is alarm/error X" pattern
    if re.search(r'what\s+is\s+(alarm|error|fault|code)\s+[a-z]?\d+', query_lower, re.IGNORECASE):
        return "error_code"
    
    # General error code pattern
    if re.search(r'\b(error|fault|alarm|code)\b.*\b[a-z0-9]{2,}\b', query_lower, re.IGNORECASE):
        return "error_code"
    
    # Troubleshooting
    if any(word in query_lower for word in [
        'not working', 'fail', 'stuck', 'issue', 'problem', 'wrong',
        'broken', 'malfunction', 'stopped', 'won\'t', 'doesn\'t', 'can\'t'
    ]):
        return "troubleshooting"
    
    # How-to
    if any(word in query_lower for word in ['how to', 'how do', 'procedure', 'steps', 'calibrate', 'setup', 'configure']):
        return "how_to"
    
    # Info request
    if any(word in query_lower for word in ['what is', 'what does', 'explain', 'describe', 'definition', 'meaning']):
        return "info"
    
    # Greeting
    if query_lower.strip() in ['hi', 'hello', 'hey', 'help']:
        return "greeting"
    
    # Vague
    if len(query.split()) < 4:
        return "vague"
    
    return "general"


def expand_query(query: str, query_type: str) -> List[str]:
    """Generate query variations to improve retrieval."""
    variations = [query]
    
    if query_type == "error_code":
        # Extract error code with better pattern matching
        # Match patterns like: 19.1, E9, AL.19.1, error 19.1, alarm 19.1
        match = re.search(r'\b([a-z]?\d+\.?\d*)\b', query, re.IGNORECASE)
        if match:
            code = match.group(1)
            variations.append(f"error {code}")
            variations.append(f"alarm {code}")
            variations.append(f"fault {code}")
            variations.append(f"code {code}")
            variations.append(f"AL.{code}")
            variations.append(f"AL. {code}")
    
    elif query_type == "troubleshooting":
        # Add symptom-focused variations
        variations.append(f"troubleshoot {query}")
        variations.append(f"fix {query}")
        variations.append(f"resolve {query}")
    
    elif query_type == "how_to":
        # Add procedure-focused variations
        variations.append(f"procedure {query}")
        variations.append(f"steps {query}")
    
    return variations


class AgentState(TypedDict):
    query: str
    query_type: str
    context: List[str]
    sources: List[Dict]
    response: str


class ProductionRAGAgent:
    """Production-ready RAG agent with improved accuracy."""
    
    def __init__(self):
        print("[*] Initializing Production RAG Agent (Improved)...")
        print(f"   Embedding: {EMBEDDING_MODEL}")
        print(f"   LLM: {LLM_MODEL}")
        
        # Initialize conversation history storage
        self.conversations = {}  # session_id -> list of messages
        print(f"   Retrieval: top_k={TOP_K}, threshold={RELEVANCE_THRESHOLD}")
        
        # Load embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 16}
        )
        
        # Load vector store
        self.vectorstore = Chroma(
            persist_directory=VECTORDB_DIR,
            embedding_function=self.embeddings
        )
        
        # Load LLM with strict settings for factual responses
        self.llm = OllamaLLM(
            model=LLM_MODEL,
            temperature=0.0,  # Zero temperature for deterministic, fact-based responses
            num_predict=500,  # Optimized for faster response
            top_k=10,
            top_p=0.9,
            repeat_penalty=1.1  # Prevent repetition
        )
        
        # Build agent graph
        self._build_graph()
        
        print("[OK] Agent ready!\n")
    
    def _retrieve_with_expansion(self, query: str, query_type: str) -> Tuple[List[str], List[Dict]]:
        """Retrieve with query expansion and hybrid scoring."""
        
        # Generate query variations
        variations = expand_query(query, query_type)
        
        all_docs = []
        seen_content = set()
        
        # Retrieve for each variation
        for var in variations[:3]:  # Limit to top 3 variations
            try:
                results = self.vectorstore.similarity_search_with_relevance_scores(
                    var,
                    k=TOP_K
                )
                
                for doc, score in results:
                    # Filter by relevance threshold
                    if score >= RELEVANCE_THRESHOLD:
                        content = doc.page_content
                        # Avoid duplicates
                        if content not in seen_content:
                            seen_content.add(content)
                            all_docs.append((doc, score))
            except Exception as e:
                print(f"[Warning] Retrieval failed for '{var}': {e}")
        
        # Sort by score and take top K (with smaller corpus, we can afford more docs)
        all_docs.sort(key=lambda x: x[1], reverse=True)
        top_docs = all_docs[:TOP_K]  # Now retrieves 8 chunks instead of 6
        
        # Extract contexts and sources
        contexts = []
        sources = []
        
        for doc, score in top_docs:
            contexts.append(doc.page_content)
            
            # Extract metadata
            metadata = doc.metadata
            source_info = {
                'file': metadata.get('source', 'unknown'),
                'page': metadata.get('page', 'N/A'),
                'score': round(score, 3)
            }
            sources.append(source_info)
        
        print(f"[Retrieval] Found {len(contexts)} relevant chunks (threshold={RELEVANCE_THRESHOLD})")
        for i, src in enumerate(sources[:3]):
            print(f"   {i+1}. {src['file']} p{src['page']} (score={src['score']})")
        
        return contexts, sources
    
    def _build_graph(self):
        """Build LangGraph workflow."""
        
        def retrieve(state: AgentState):
            query = state["query"]
            query_type = classify_query(query)
            
            contexts, sources = self._retrieve_with_expansion(query, query_type)
            
            return {
                "query_type": query_type,
                "context": contexts,
                "sources": sources
            }
        
        def generate_response(state: AgentState):
            query = state['query']
            query_type = state['query_type']
            contexts = state['context']
            sources = state['sources']
            
            # Check hardcoded error database first for known errors
            if query_type == "error_code":
                # Extract error code from query
                error_match = re.search(r'\b([a-z]?\d+\.?\d*)\b', query, re.IGNORECASE)
                if error_match:
                    error_code = error_match.group(1).lower()
                    # Check if this error code is in our hardcoded database
                    if error_code in ERROR_CODE_DATABASE:
                        print(f"[Hardcoded Lookup] Found error code {error_code} in database")
                        return {"response": ERROR_CODE_DATABASE[error_code]["content"]}
            
            # Handle special cases
            if query_type == "greeting":
                return {"response": "Hello! I'm a troubleshooting assistant for industrial paint defect detection systems. I can help with error codes, camera issues, defect detection problems, and maintenance procedures. What specific issue are you facing?"}
            
            if query_type == "vague":
                return {"response": "I'd be happy to help! Could you provide more details about your specific issue? For example, are you experiencing an error code, camera problems, or defect detection issues?"}
            
            # Build context text with clear formatting (use more chunks with optimized corpus)
            if not contexts:
                context_text = "No specific documentation found for this query."
            else:
                # Format context with clear chunk separators and numbering
                formatted_contexts = []
                for i, ctx in enumerate(contexts[:6], 1):
                    formatted_contexts.append(f"[CHUNK {i}]\n{ctx}\n[END CHUNK {i}]")
                context_text = "\n\n".join(formatted_contexts)
            
            # Build source references
            source_refs = []
            for src in sources[:6]:  # Show more sources with optimized retrieval
                source_refs.append(f"{src['file']} p{src['page']}")
            source_text = ", ".join(source_refs) if source_refs else "No sources"
            
            # Select prompt template based on query type
            if query_type == "error_code":
                prompt = f"""You are a technical troubleshooting expert. Answer ONLY using the provided documentation below.

User Query: {query}

=== DOCUMENTATION (YOU MUST USE THIS EXACT TEXT) ===
{context_text}
=== END DOCUMENTATION ===

CRITICAL INSTRUCTIONS:
1. You MUST quote or paraphrase the exact text from the documentation above
2. DO NOT make up information or use general knowledge
3. If the documentation doesn't contain the answer, say "The provided documentation does not contain information about this error code"
4. Extract specific details, numbers, steps, and procedures directly from the documentation
5. Your answer must be traceable back to the documentation text

Provide your response in HTML format:

<div class="error-response">
  <div class="error-details">
    <strong>Error Code:</strong>
    <p>[Extract exact error code and description from documentation]</p>
  </div>
  <div class="cause">
    <strong>Possible Cause:</strong>
    <p>[Quote or closely paraphrase the cause from documentation]</p>
  </div>
  <div class="solution">
    <strong>Solution Steps:</strong>
    <ol>
      <li>[Extract step 1 from documentation]</li>
      <li>[Extract step 2 from documentation]</li>
      <li>[Extract step 3 from documentation]</li>
    </ol>
  </div>
  <div class="source-ref">Source: {source_text}</div>
</div>

REMEMBER: Use ONLY the documentation text above. Do not add generic advice."""
            
            elif query_type == "troubleshooting":
                prompt = f"""You are a technical troubleshooting expert. Answer ONLY using the provided documentation below.

User Issue: {query}

=== DOCUMENTATION (YOU MUST USE THIS EXACT TEXT) ===
{context_text}
=== END DOCUMENTATION ===

CRITICAL INSTRUCTIONS:
1. Extract troubleshooting steps DIRECTLY from the documentation above
2. Quote specific procedures, settings, or values mentioned in the documentation
3. DO NOT provide generic troubleshooting advice
4. If the documentation doesn't address this issue, say "The provided documentation does not contain specific troubleshooting steps for this issue"
5. Include exact technical details (part numbers, settings, measurements) from the documentation

Provide your response in HTML:

<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>[Describe based on documentation context]</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps (from documentation):</strong>
    <ol>
      <li>[Extract exact step 1 from documentation]</li>
      <li>[Extract exact step 2 from documentation]</li>
      <li>[Extract exact step 3 from documentation]</li>
      <li>[Add more steps if found in documentation]</li>
    </ol>
  </div>
  <div class="source-ref">Source: {source_text}</div>
</div>

REMEMBER: Every step must come from the documentation above. No generic advice."""
            
            elif query_type == "how_to":
                prompt = f"""You are a technical expert. Answer ONLY using the provided documentation below.

User Question: {query}

=== DOCUMENTATION (YOU MUST USE THIS EXACT TEXT) ===
{context_text}
=== END DOCUMENTATION ===

CRITICAL INSTRUCTIONS:
1. Extract the procedure DIRECTLY from the documentation above
2. Copy the exact steps, settings, and parameters from the documentation
3. Include specific values, measurements, or technical details mentioned
4. DO NOT add generic how-to steps from general knowledge
5. If the procedure is not in the documentation, say "The provided documentation does not contain a procedure for this task"

Provide your response in HTML:

<div class="procedure-response">
  <div class="overview">
    <strong>Procedure (from documentation):</strong>
    <p>[Extract overview from documentation]</p>
  </div>
  <div class="steps">
    <strong>Steps:</strong>
    <ol>
      <li>[Copy exact step 1 from documentation with all details]</li>
      <li>[Copy exact step 2 from documentation with all details]</li>
      <li>[Copy exact step 3 from documentation with all details]</li>
    </ol>
  </div>
  <div class="notes">
    <strong>Notes:</strong>
    <p>[Extract warnings or notes from documentation]</p>
  </div>
  <div class="source-ref">Source: {source_text}</div>
</div>

REMEMBER: Every detail must come from the documentation. Quote exact values and settings."""
            
            elif query_type == "info":
                prompt = f"""You are a technical expert. Answer ONLY using the provided documentation below.

User Question: {query}

=== DOCUMENTATION (YOU MUST USE THIS EXACT TEXT) ===
{context_text}
=== END DOCUMENTATION ===

CRITICAL INSTRUCTIONS:
1. Answer by quoting or closely paraphrasing the documentation above
2. Include specific technical details, definitions, or specifications from the documentation
3. DO NOT provide general explanations - use the exact information from the documentation
4. If the answer is not in the documentation, say "The provided documentation does not contain this information"
5. Reference specific sections or details from the documentation in your answer

Provide your response in HTML:

<div class="info-response">
  <div class="answer">
    <p>[Extract and explain using exact text from documentation]</p>
  </div>
  <div class="source-ref">Source: {source_text}</div>
</div>

REMEMBER: Your answer must be traceable to the documentation text above."""
            
            else:  # general
                prompt = f"""You are a technical expert. Answer ONLY using the provided documentation below.

User Question: {query}

=== DOCUMENTATION (YOU MUST USE THIS EXACT TEXT) ===
{context_text}
=== END DOCUMENTATION ===

CRITICAL INSTRUCTIONS:
1. Base your entire answer on the documentation above
2. Quote specific passages, procedures, or technical details from the documentation
3. DO NOT use general knowledge or make assumptions
4. If the documentation doesn't fully answer the question, say "Based on the provided documentation..." and explain what IS covered
5. Include exact technical specifications, part numbers, or settings mentioned in the documentation

Provide your response in HTML:

<div class="general-response">
  <div class="answer">
    <p>[Provide comprehensive answer using exact information from documentation]</p>
  </div>
  <div class="source-ref">Source: {source_text}</div>
</div>

REMEMBER: Every fact in your answer must come from the documentation above. Be specific and detailed."""
            
            response = self.llm.invoke(prompt)
            return {"response": response}
        
        graph = StateGraph(AgentState)
        graph.add_node("retrieve", retrieve)
        graph.add_node("generate", generate_response)
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "generate")
        
        self.agent = graph.compile()
    
    def _clean_response(self, response: str) -> str:
        """Clean markdown artifacts from response."""
        response = response.strip()
        if response.startswith("```html"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        return response.strip()
    
    def query(self, question: str, session_id: str = "default") -> str:
        """Query the agent with conversation history support."""
        # Get or create conversation history for this session
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        result = self.agent.invoke({"query": question})
        raw_response = result["response"]
        cleaned = self._clean_response(raw_response)
        
        # Store this exchange in history
        self.conversations[session_id].append({"role": "user", "content": question})
        self.conversations[session_id].append({"role": "assistant", "content": cleaned})
        
        # Keep only last 10 exchanges (20 messages)
        if len(self.conversations[session_id]) > 20:
            self.conversations[session_id] = self.conversations[session_id][-20:]
        
        return cleaned
    
    def clear_history(self, session_id: str = "default"):
        """Clear conversation history for a session."""
        if session_id in self.conversations:
            self.conversations[session_id] = []
            print(f"[*] Cleared conversation history for session: {session_id}")
    
    def get_history(self, session_id: str = "default") -> List[Dict]:
        """Get conversation history for a session."""
        return self.conversations.get(session_id, [])


# Singleton instance
_agent_instance = None

def get_agent():
    """Get or create agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ProductionRAGAgent()
    return _agent_instance


# Export classify_query for testing
__all__ = ['get_agent', 'ProductionRAGAgent', 'classify_query']


if __name__ == "__main__":
    agent = get_agent()
    
    test_queries = [
        "What is error code 1A68H?",
        "Camera is not detecting defects properly",
        "How to calibrate the vision system?",
        "What does the light intensity parameter do?",
        "Paint finish looks uneven"
    ]
    
    print("=" * 70)
    print("TESTING IMPROVED AGENT")
    print("=" * 70 + "\n")
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print(f"Type: {classify_query(query)}")
        print("-" * 70)
        response = agent.query(query)
        print(response[:200] + "..." if len(response) > 200 else response)
        print("\n" + "=" * 70)
