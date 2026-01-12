import { app, BrowserWindow } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow;
let pythonProcess = null;

function startPythonBackend() {
  const ragPath = path.join(__dirname, '../production_rag');
  const scriptPath = path.join(ragPath, 'fastapi_server.py');
  
  console.log('Starting RAG backend server...');
  
  pythonProcess = spawn('python', [scriptPath], {
    cwd: ragPath,
    stdio: ['pipe', 'pipe', 'pipe']
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[RAG Server] ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[RAG Server Error] ${data.toString().trim()}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`RAG server exited with code ${code}`);
    pythonProcess = null;
  });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start RAG server:', err);
  });
}

function stopPythonBackend() {
  if (pythonProcess) {
    console.log('Stopping RAG backend server...');
    pythonProcess.kill();
    pythonProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false, // For simple migration. Security headers recommended for prod.
    },
    autoHideMenuBar: true, // Optional: Hide the default menu bar
  });

  const startUrl = process.env.ELECTRON_START_URL || `file://${path.join(__dirname, '../dist/index.html')}`;

  mainWindow.loadURL(startUrl);

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

app.on('ready', () => {
  startPythonBackend();
  createWindow();
});

app.on('window-all-closed', function () {
  stopPythonBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopPythonBackend();
});

app.on('activate', function () {
  if (mainWindow === null) {
    createWindow();
  }
});
