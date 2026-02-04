import { app, BrowserWindow } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn, exec } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow;
let pythonProcess = null;
let isStopping = false;

function cleanupPythonProcesses() {
  return new Promise((resolve) => {
    // Windows only: Kill all python processes to ensure clean slate
    if (process.platform === 'win32') {
      console.log('Cleaning up existing Python processes...');
      exec('taskkill /F /IM python.exe /T', (error, stdout, stderr) => {
        // Ignore errors (e.g. if no process found)
        resolve();
      });
    } else {
      resolve();
    }
  });
}

function startPythonBackend() {
  const backendPath = path.join(__dirname, '../backend');
  const scriptPath = path.join(backendPath, 'main.py');

  console.log('Starting Unified Backend Server...');

  pythonProcess = spawn('python', [scriptPath], {
    cwd: backendPath,
    stdio: ['pipe', 'pipe', 'pipe']
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Python Server] ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[Python Server Error] ${data.toString().trim()}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python server exited with code ${code}`);
    pythonProcess = null;
  });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python server:', err);
  });
}

function stopPythonBackend() {
  if (pythonProcess && !isStopping) {
    isStopping = true;
    console.log('Stopping Python backend server...');
    // Robust kill for Windows (Tree kill)
    if (process.platform === 'win32') {
      exec(`taskkill /pid ${pythonProcess.pid} /T /F`, (err) => {
        if (err) {
          console.log("Process might have already exited");
          try { pythonProcess.kill(); } catch (e) { }
        }
        pythonProcess = null;
      });
    } else {
      pythonProcess.kill();
      pythonProcess = null;
    }
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webSecurity: false,
      cache: false,
    },
    autoHideMenuBar: true,
  });

  const startUrl = process.env.ELECTRON_START_URL || `file://${path.join(__dirname, '../dist/index.html')}`;

  mainWindow.loadURL(startUrl);

  // Open DevTools in development mode
  if (process.env.ELECTRON_START_URL) {
    mainWindow.webContents.openDevTools();
  }

  // Force reload to clear any cached content
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.session.clearCache();
  });

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

app.on('ready', async () => {
  await cleanupPythonProcesses();
  startPythonBackend();
  createWindow();
  mainWindow.webContents.session.clearCache();
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