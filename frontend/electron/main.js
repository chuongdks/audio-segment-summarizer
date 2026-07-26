import { app, BrowserWindow, shell } from "electron";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const isDev = !app.isPackaged;

function createWindow() {
  const win = new BrowserWindow({
    width: 960,
    height: 800,
    minWidth: 720,
    minHeight: 600,
    backgroundColor: "#0f1117",
    titleBarStyle: "hiddenInset",  // clean frameless look on Mac; ignored on Windows
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  if (isDev) {
    // In dev: load from Vite dev server
    win.loadURL("http://localhost:5173");
  } else {
    // In production: load built files
    win.loadFile(path.join(__dirname, "../dist/index.html"));
  }

  // Open external links in the system browser, not in Electron
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
