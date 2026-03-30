const { app, BrowserWindow, Tray, Menu, ipcMain, Notification } = require('electron');
const path = require('path');
const Store = require('electron-store');
const https = require('https');

const store = new Store();
let mainWindow = null;
let tray = null;
let sseConnection = null;

// Ignore SSL errors for self-signed Hue bridge cert
app.commandLine.appendSwitch('ignore-certificate-errors');

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 480,
    height: 600,
    resizable: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
    titleBarStyle: 'hiddenInset',
    show: false,
  });

  mainWindow.loadFile('index.html');
  
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

function createTray() {
  // TODO: Add proper icon
  tray = new Tray(path.join(__dirname, 'assets', 'tray-icon.png'));
  
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Open Hue Monitor', click: () => mainWindow.show() },
    { type: 'separator' },
    { label: 'Start Monitoring', click: () => startMonitoring() },
    { label: 'Stop Monitoring', click: () => stopMonitoring() },
    { type: 'separator' },
    { label: 'Quit', click: () => { app.isQuitting = true; app.quit(); } }
  ]);
  
  tray.setToolTip('Hue Monitor');
  tray.setContextMenu(contextMenu);
  
  tray.on('click', () => {
    mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
  });
}

function showNotification(title, body) {
  new Notification({ title, body }).show();
}

function startMonitoring() {
  const bridgeIp = store.get('bridge.ip');
  const bridgeKey = store.get('bridge.key');
  const sensors = store.get('sensors', []);
  
  if (!bridgeIp || !bridgeKey) {
    showNotification('Hue Monitor', 'Bridge not configured');
    return;
  }
  
  if (sensors.length === 0) {
    showNotification('Hue Monitor', 'No sensors configured');
    return;
  }
  
  const monitoredIds = new Set(sensors.map(s => s.id));
  
  const options = {
    hostname: bridgeIp,
    port: 443,
    path: '/eventstream/clip/v2',
    method: 'GET',
    headers: {
      'hue-application-key': bridgeKey,
      'Accept': 'text/event-stream'
    },
    rejectUnauthorized: false
  };
  
  sseConnection = https.request(options, (res) => {
    console.log('Connected to SSE stream');
    
    res.on('data', (chunk) => {
      const lines = chunk.toString().split('\n');
      
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        
        try {
          const events = JSON.parse(line.slice(6));
          
          for (const event of events) {
            if (event.type !== 'update') continue;
            
            for (const item of event.data || []) {
              if (item.type !== 'contact') continue;
              if (!monitoredIds.has(item.id)) continue;
              
              const state = item.contact_report?.state;
              if (state === 'no_contact') {
                const sensor = sensors.find(s => s.id === item.id);
                const name = sensor?.name || 'Unknown';
                showNotification('🚪 Door Opened', `${name} was opened`);
                
                // Send to renderer
                mainWindow?.webContents.send('door-event', {
                  sensor: name,
                  state: 'open',
                  timestamp: new Date().toISOString()
                });
              }
            }
          }
        } catch (e) {
          // Ignore parse errors
        }
      }
    });
    
    res.on('end', () => {
      console.log('SSE connection closed, reconnecting...');
      setTimeout(startMonitoring, 5000);
    });
  });
  
  sseConnection.on('error', (e) => {
    console.error('SSE error:', e.message);
    setTimeout(startMonitoring, 5000);
  });
  
  sseConnection.end();
}

function stopMonitoring() {
  if (sseConnection) {
    sseConnection.destroy();
    sseConnection = null;
  }
}

// IPC handlers
ipcMain.handle('get-config', () => store.store);
ipcMain.handle('set-config', (_, key, value) => store.set(key, value));
ipcMain.handle('discover-bridges', async () => {
  return new Promise((resolve) => {
    https.get('https://discovery.meethue.com', (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve([]);
        }
      });
    }).on('error', () => resolve([]));
  });
});

ipcMain.handle('pair-bridge', async (_, ip) => {
  return new Promise((resolve) => {
    const payload = JSON.stringify({
      devicetype: 'hue-monitor#electron',
      generateclientkey: true
    });
    
    const req = https.request({
      hostname: ip,
      port: 443,
      path: '/api',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      rejectUnauthorized: false
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          if (result[0]?.success?.username) {
            resolve({ success: true, key: result[0].success.username });
          } else {
            resolve({ success: false, error: result[0]?.error?.description });
          }
        } catch {
          resolve({ success: false, error: 'Parse error' });
        }
      });
    });
    
    req.on('error', (e) => resolve({ success: false, error: e.message }));
    req.write(payload);
    req.end();
  });
});

ipcMain.handle('get-sensors', async (_, ip, key) => {
  return new Promise((resolve) => {
    const req = https.request({
      hostname: ip,
      port: 443,
      path: '/clip/v2/resource/contact',
      method: 'GET',
      headers: { 'hue-application-key': key },
      rejectUnauthorized: false
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          resolve(result.data || []);
        } catch {
          resolve([]);
        }
      });
    });
    
    req.on('error', () => resolve([]));
    req.end();
  });
});

ipcMain.handle('start-monitoring', () => startMonitoring());
ipcMain.handle('stop-monitoring', () => stopMonitoring());

app.whenReady().then(() => {
  createWindow();
  createTray();
  
  // Auto-start monitoring if configured
  if (store.get('autoStart') && store.get('bridge.ip') && store.get('sensors', []).length > 0) {
    startMonitoring();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  } else {
    mainWindow.show();
  }
});
