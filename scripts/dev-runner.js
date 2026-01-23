import { createServer } from 'net';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');

// Helper to find a free port
const findFreePort = () => new Promise((resolve, reject) => {
    const server = createServer();
    server.unref();
    server.on('error', reject);
    server.listen(0, () => {
        const port = server.address().port;
        server.close(() => {
            resolve(port);
        });
    });
});

async function start() {
    try {
        const port = await findFreePort();
        console.log(`[DevRunner] Found free port for Frontend: ${port}`);

        // 1. Start Vite
        const vite = spawn('npm.cmd', ['run', 'dev', '--', '--port', port.toString(), '--strictPort'], {
            cwd: rootDir,
            stdio: 'inherit',
            shell: true,
            env: { ...process.env, FORCE_COLOR: 'true' }
        });

        // Wait a bit for Vite to start
        await new Promise(r => setTimeout(r, 2000));

        // 2. Start Electron
        console.log(`[DevRunner] Starting Electron...`);
        const electron = spawn('npm.cmd', ['exec', 'electron', '.'], {
            cwd: rootDir,
            stdio: 'inherit',
            shell: true,
            env: {
                ...process.env,
                ELECTRON_START_URL: `http://localhost:${port}`,
                FORCE_COLOR: 'true'
            }
        });

        electron.on('close', (code) => {
            console.log(`[DevRunner] Electron exited with code ${code}`);
            vite.kill();
            process.exit(code);
        });

    } catch (err) {
        console.error('Failed to start dev environment:', err);
        process.exit(1);
    }
}

start();
