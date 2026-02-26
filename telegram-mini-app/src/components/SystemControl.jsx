/**
 * 📱 JARVIS System Control — Phone & PC Control Panel
 * ════════════════════════════════════════════════════
 * 
 * Full device control from JARVIS:
 * - Volume control
 * - Brightness control
 * - Flashlight toggle
 * - Battery status
 * - Network info
 * - App launcher
 * - Phone calls
 * - Device vibration
 * - PC power control (desktop)
 * - Screenshot capture (desktop)
 */

import React, { useState, useEffect, useCallback } from 'react';

// Icons
const icons = {
  volume: '🔊', volumeMute: '🔇', brightness: '☀️', flashlight: '🔦',
  battery: '🔋', wifi: '📶', phone: '📞', vibrate: '📳',
  power: '⚡', screenshot: '📸', apps: '📱', music: '🎵',
  shutdown: '🔴', restart: '🔄', sleep: '😴', lock: '🔒',
  whatsapp: '💬', youtube: '▶️', chrome: '🌐', settings: '⚙️',
  cpu: '🖥️', memory: '🧠', disk: '💾', network: '🌐',
};

const SystemControl = () => {
  const [battery, setBattery] = useState(null);
  const [network, setNetwork] = useState(null);
  const [volume, setVolume] = useState(50);
  const [brightness, setBrightness] = useState(80);
  const [flashlightOn, setFlashlightOn] = useState(false);
  const [systemSpecs, setSystemSpecs] = useState(null);
  const [activeTab, setActiveTab] = useState('controls');
  const [notification, setNotification] = useState('');
  const [error, setError] = useState('');

  // Platform detection - safe, no state updates during render
  let isDesktop = false, isNative = false;
  try {
    isDesktop = typeof window !== 'undefined' && !!window.jarvisDesktop?.isDesktop;
    isNative = typeof window !== 'undefined' && !!window.Capacitor?.isNativePlatform?.();
  } catch (e) {
    // Will set error in useEffect
    console.warn('Platform detection failed:', e);
  }

  // Load device info on mount
  useEffect(() => {
    try {
      loadDeviceInfo();
      const interval = setInterval(loadDeviceInfo, 10000);
      return () => clearInterval(interval);
    } catch (e) {
      setError('Init failed: ' + (e?.message || e));
    }
  }, []);

  const showNotif = useCallback((msg) => {
    setNotification(msg);
    setTimeout(() => setNotification(''), 2500);
  }, []);

  const loadDeviceInfo = async () => {
    // Battery
    try {
      if (isNative) {
        const { Capacitor } = await import('@capacitor/core');
        const DeviceCommands = Capacitor.Plugins.DeviceCommands;
        if (DeviceCommands?.getBattery) {
          const b = await DeviceCommands.getBattery();
          setBattery(b);
        }
      } else if (navigator.getBattery) {
        const b = await navigator.getBattery();
        setBattery({
          level: Math.round(b.level * 100),
          isCharging: b.charging,
          status: b.charging ? 'Charging' : 'Discharging',
        });
      } else if (isDesktop) {
        const info = await window.jarvisDesktop.getBatteryInfo();
        setBattery({ level: '--', status: info?.data || 'N/A', raw: info?.data });
      }
    } catch (e) {
      setError('Battery info failed: ' + (e?.message || e));
    }

    // Network
    try {
      if (isNative) {
        const { Capacitor } = await import('@capacitor/core');
        const DeviceCommands = Capacitor.Plugins.DeviceCommands;
        if (DeviceCommands?.getNetwork) {
          const n = await DeviceCommands.getNetwork();
          setNetwork(n);
        }
      } else {
        setNetwork({
          connected: navigator.onLine,
          type: navigator.connection?.effectiveType || 'Unknown',
          downlink: navigator.connection?.downlink || '--',
        });
      }
    } catch (e) {
      setError('Network info failed: ' + (e?.message || e));
    }

    // System specs (desktop)
    if (isDesktop) {
      try {
        const specs = await window.jarvisDesktop.getOsSpecs();
        setSystemSpecs(specs);
      } catch (e) {
        setError('System specs failed: ' + (e?.message || e));
      }
    }
  };

  // ═══ CONTROL ACTIONS ═══

  const handleVolumeChange = async (newVol) => {
    setVolume(newVol);
    try {
      if (isDesktop && window.jarvisDesktop?.volumeSet) {
        await window.jarvisDesktop.volumeSet(newVol);
      } else if (isNative) {
        const { Capacitor } = await import('@capacitor/core');
        if (Capacitor?.Plugins?.DeviceCommands?.setVolume) {
          await Capacitor.Plugins.DeviceCommands.setVolume({ level: newVol });
        } else {
          setError('DeviceCommands.setVolume not available');
        }
      } else {
        setError('Volume control not supported in this environment');
      }
      showNotif(`Volume: ${newVol}%`);
    } catch (e) {
      setError('Volume error: ' + (e?.message || e));
    }
  };

  const handleBrightnessChange = async (newBr) => {
    setBrightness(newBr);
    try {
      if (isDesktop && window.jarvisDesktop?.brightnessSet) {
        await window.jarvisDesktop.brightnessSet(newBr);
      } else if (isNative) {
        const { Capacitor } = await import('@capacitor/core');
        if (Capacitor?.Plugins?.DeviceCommands?.setBrightness) {
          await Capacitor.Plugins.DeviceCommands.setBrightness({ level: newBr });
        } else {
          setError('DeviceCommands.setBrightness not available');
        }
      } else {
        setError('Brightness control not supported in this environment');
      }
      showNotif(`Brightness: ${newBr}%`);
    } catch (e) {
      setError('Brightness error: ' + (e?.message || e));
    }
  };

  const toggleFlashlight = async () => {
    try {
      if (isNative) {
        const { Capacitor } = await import('@capacitor/core');
        if (Capacitor?.Plugins?.DeviceCommands?.toggleFlashlight) {
          await Capacitor.Plugins.DeviceCommands.toggleFlashlight();
          setFlashlightOn(!flashlightOn);
          showNotif(flashlightOn ? 'Flashlight OFF' : 'Flashlight ON');
        } else {
          setError('DeviceCommands.toggleFlashlight not available');
        }
      } else {
        setError('Flashlight not supported in this environment');
      }
    } catch (e) { setError('Flashlight error: ' + (e?.message || e)); }
  };

  const vibrate = () => {
    try {
      if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100, 50, 200]);
        showNotif('Vibration sent!');
      }
    } catch {}
  };

  const openApp = async (appName) => {
    try {
      if (isDesktop && window.jarvisDesktop?.openApp) {
        await window.jarvisDesktop.openApp(appName);
        showNotif(`Opening ${appName}...`);
      } else if (isNative) {
        const { Capacitor } = await import('@capacitor/core');
        if (Capacitor?.Plugins?.DeviceCommands?.openApp) {
          await Capacitor.Plugins.DeviceCommands.openApp({ packageName: appName });
          showNotif(`Opening ${appName}...`);
        } else {
          setError('DeviceCommands.openApp not available');
        }
      } else {
        setError('App launch not supported in this environment');
      }
    } catch (e) { setError(`Can't open ${appName}: ` + (e?.message || e)); }
  };

  const pcAction = async (action) => {
    if (!isDesktop) { showNotif('PC control only on desktop'); return; }
    try {
      if (window.jarvisDesktop?.[action]) {
        const result = await window.jarvisDesktop[action]();
        showNotif(result?.message || `${action} executed`);
      } else {
        setError(`jarvisDesktop.${action} not available`);
      }
    } catch (e) { setError(`${action} failed: ` + (e?.message || e)); }
  };

  const takeScreenshot = async () => {
    if (!isDesktop) { showNotif('Screenshots only on desktop'); return; }
    try {
      if (window.jarvisDesktop?.captureScreen) {
        const result = await window.jarvisDesktop.captureScreen();
        if (result?.success && result.image) {
          // Open in new window
          const w = window.open('', '_blank');
          if (w) {
            w.document.write(`<img src="${result.image}" style="max-width:100%">`);
          }
          showNotif('Screenshot captured!');
        }
      } else {
        setError('jarvisDesktop.captureScreen not available');
      }
    } catch (e) { setError('Screenshot failed: ' + (e?.message || e)); }
  };

  const makeCall = async (number) => {
    try {
      if (isNative) {
        const { Capacitor } = await import('@capacitor/core');
        const DeviceCommands = Capacitor.Plugins.DeviceCommands;
        await DeviceCommands?.makeCall?.({ number });
      } else {
        window.open(`tel:${number}`);
      }
      showNotif(`Calling ${number}...`);
    } catch { showNotif('Call failed'); }
  };

  // ═══ STYLES ═══
  const styles = {
    container: {
      minHeight: '100vh', background: 'linear-gradient(135deg, #0a0e1a 0%, #0d1421 50%, #0a1628 100%)',
      color: '#fff', padding: '16px', paddingBottom: '80px',
    },
    header: {
      textAlign: 'center', marginBottom: '20px',
    },
    title: {
      fontSize: '24px', fontWeight: '700', color: '#00a8ff',
      textShadow: '0 0 20px rgba(0,168,255,0.5)',
    },
    subtitle: {
      fontSize: '12px', color: 'rgba(255,255,255,0.5)', letterSpacing: '2px',
    },
    notif: {
      position: 'fixed', top: '60px', left: '50%', transform: 'translateX(-50%)',
      background: 'rgba(0,168,255,0.9)', color: '#fff', padding: '8px 20px',
      borderRadius: '20px', fontSize: '13px', fontWeight: '600', zIndex: 10000,
      boxShadow: '0 4px 20px rgba(0,168,255,0.4)', display: notification ? 'block' : 'none',
    },
    tabs: {
      display: 'flex', gap: '8px', marginBottom: '16px', overflowX: 'auto',
      paddingBottom: '4px',
    },
    tab: {
      padding: '8px 16px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)',
      background: 'transparent', color: 'rgba(255,255,255,0.6)', fontSize: '12px',
      cursor: 'pointer', whiteSpace: 'nowrap', fontWeight: '600',
    },
    tabActive: {
      background: 'rgba(0,168,255,0.2)', color: '#00a8ff',
      borderColor: 'rgba(0,168,255,0.4)',
    },
    grid: {
      display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
      gap: '12px',
    },
    card: {
      background: 'rgba(255,255,255,0.05)', borderRadius: '16px',
      padding: '16px', textAlign: 'center', cursor: 'pointer',
      border: '1px solid rgba(255,255,255,0.08)',
      transition: 'all 0.2s',
    },
    cardIcon: { fontSize: '28px', marginBottom: '8px' },
    cardLabel: { fontSize: '12px', color: 'rgba(255,255,255,0.7)', fontWeight: '600' },
    cardValue: { fontSize: '16px', color: '#00a8ff', fontWeight: '700', marginTop: '4px' },
    slider: {
      width: '100%', marginTop: '8px', accentColor: '#00a8ff',
    },
    section: {
      marginBottom: '20px',
    },
    sectionTitle: {
      fontSize: '14px', color: 'rgba(255,255,255,0.5)', fontWeight: '600',
      letterSpacing: '1px', marginBottom: '12px', textTransform: 'uppercase',
    },
  };

  return (
    <div style={styles.container}>
      {/* Notification Toast */}
      <div style={styles.notif}>{notification}</div>
      {/* Error Toast */}
      {error && (
        <div style={{...styles.notif, background: 'rgba(255,68,68,0.95)', top: '100px'}}>
          <b>JS Error:</b> {error}
        </div>
      )}

      {/* Header */}
      <div style={styles.header}>
        <div style={styles.title}>⚡ System Control</div>
        <div style={styles.subtitle}>
          {isDesktop ? 'PC CONTROL MODE' : isNative ? 'PHONE CONTROL MODE' : 'WEB MODE'}
        </div>
      </div>

      {/* Fallback for unsupported environments */}
      {!(isDesktop || isNative) && (
        <div style={{color:'#ff4444',textAlign:'center',margin:'32px 0',fontWeight:600}}>
          ⚠️ Full system control is only available in the JARVIS OS desktop app or Android app.<br/>
          Most controls will not work in the web browser.<br/>
          <span style={{fontSize:'12px',color:'#fff'}}>If you see errors, check your build or platform integration.</span>
        </div>
      )}

      {/* Tabs */}
      <div style={styles.tabs}>
        {['controls', 'status', 'apps', isDesktop && 'pc-power'].filter(Boolean).map(tab => (
          <button
            key={tab}
            style={{...styles.tab, ...(activeTab === tab ? styles.tabActive : {})}}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'controls' ? '🎛️ Controls' : tab === 'status' ? '📊 Status' : tab === 'apps' ? '📱 Apps' : '💻 PC Power'}
          </button>
        ))}
      </div>

      {/* Controls Tab */}
      {activeTab === 'controls' && (
        <>
          <div style={styles.section}>
            <div style={styles.sectionTitle}>Audio & Display</div>
            <div style={styles.grid}>
              <div style={styles.card}>
                <div style={styles.cardIcon}>{icons.volume}</div>
                <div style={styles.cardLabel}>Volume</div>
                <div style={styles.cardValue}>{volume}%</div>
                <input type="range" min="0" max="100" value={volume}
                  style={styles.slider}
                  onChange={e => handleVolumeChange(parseInt(e.target.value))} />
              </div>
              <div style={styles.card}>
                <div style={styles.cardIcon}>{icons.brightness}</div>
                <div style={styles.cardLabel}>Brightness</div>
                <div style={styles.cardValue}>{brightness}%</div>
                <input type="range" min="0" max="100" value={brightness}
                  style={styles.slider}
                  onChange={e => handleBrightnessChange(parseInt(e.target.value))} />
              </div>
              <div style={styles.card} onClick={toggleFlashlight}>
                <div style={styles.cardIcon}>{icons.flashlight}</div>
                <div style={styles.cardLabel}>Flashlight</div>
                <div style={{...styles.cardValue, color: flashlightOn ? '#ffd700' : '#666'}}>
                  {flashlightOn ? 'ON' : 'OFF'}
                </div>
              </div>
              <div style={styles.card} onClick={vibrate}>
                <div style={styles.cardIcon}>{icons.vibrate}</div>
                <div style={styles.cardLabel}>Vibrate</div>
                <div style={styles.cardValue}>TAP</div>
              </div>
            </div>
          </div>

          {isDesktop && (
            <div style={styles.section}>
              <div style={styles.sectionTitle}>Media Controls</div>
              <div style={styles.grid}>
                <div style={styles.card} onClick={() => window.jarvisDesktop?.mediaControl('previous')}>
                  <div style={styles.cardIcon}>⏮</div>
                  <div style={styles.cardLabel}>Previous</div>
                </div>
                <div style={styles.card} onClick={() => window.jarvisDesktop?.mediaControl('play')}>
                  <div style={styles.cardIcon}>⏯</div>
                  <div style={styles.cardLabel}>Play/Pause</div>
                </div>
                <div style={styles.card} onClick={() => window.jarvisDesktop?.mediaControl('next')}>
                  <div style={styles.cardIcon}>⏭</div>
                  <div style={styles.cardLabel}>Next</div>
                </div>
                <div style={styles.card} onClick={takeScreenshot}>
                  <div style={styles.cardIcon}>{icons.screenshot}</div>
                  <div style={styles.cardLabel}>Screenshot</div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Status Tab */}
      {activeTab === 'status' && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>Device Status</div>
          <div style={styles.grid}>
            <div style={styles.card}>
              <div style={styles.cardIcon}>{icons.battery}</div>
              <div style={styles.cardLabel}>Battery</div>
              <div style={styles.cardValue}>
                {battery?.level != null ? `${battery.level}%` : '--'}
              </div>
              <div style={{fontSize: '10px', color: 'rgba(255,255,255,0.4)', marginTop: '4px'}}>
                {battery?.status || battery?.isCharging ? '⚡ Charging' : ''}
              </div>
            </div>
            <div style={styles.card}>
              <div style={styles.cardIcon}>{icons.wifi}</div>
              <div style={styles.cardLabel}>Network</div>
              <div style={{...styles.cardValue, color: network?.connected ? '#00ff64' : '#ff4444'}}>
                {network?.connected ? 'Online' : 'Offline'}
              </div>
              <div style={{fontSize: '10px', color: 'rgba(255,255,255,0.4)', marginTop: '4px'}}>
                {network?.type || ''} {network?.downlink ? `${network.downlink} Mbps` : ''}
              </div>
            </div>
            {systemSpecs && (
              <>
                <div style={styles.card}>
                  <div style={styles.cardIcon}>{icons.cpu}</div>
                  <div style={styles.cardLabel}>CPU</div>
                  <div style={styles.cardValue}>{systemSpecs.cpuCount} cores</div>
                  <div style={{fontSize: '9px', color: 'rgba(255,255,255,0.4)', marginTop: '4px'}}>
                    {systemSpecs.cpuModel?.substring(0, 25)}
                  </div>
                </div>
                <div style={styles.card}>
                  <div style={styles.cardIcon}>{icons.memory}</div>
                  <div style={styles.cardLabel}>Memory</div>
                  <div style={styles.cardValue}>{systemSpecs.memoryUsagePercent}%</div>
                  <div style={{fontSize: '10px', color: 'rgba(255,255,255,0.4)', marginTop: '4px'}}>
                    {(systemSpecs.totalMemory / 1073741824).toFixed(1)} GB total
                  </div>
                </div>
                <div style={styles.card}>
                  <div style={styles.cardIcon}>{icons.power}</div>
                  <div style={styles.cardLabel}>Uptime</div>
                  <div style={styles.cardValue}>
                    {(systemSpecs.uptime / 3600).toFixed(1)}h
                  </div>
                </div>
                <div style={styles.card}>
                  <div style={styles.cardIcon}>{icons.settings}</div>
                  <div style={styles.cardLabel}>Platform</div>
                  <div style={{...styles.cardValue, fontSize: '12px'}}>
                    {systemSpecs.platform} {systemSpecs.arch}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Apps Tab */}
      {activeTab === 'apps' && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>Quick Launch</div>
          <div style={styles.grid}>
            {[
              { icon: icons.chrome, label: 'Chrome', app: 'chrome' },
              { icon: icons.whatsapp, label: 'WhatsApp', app: 'whatsapp' },
              { icon: icons.youtube, label: 'YouTube', app: isDesktop ? 'chrome' : 'youtube',
                action: isDesktop ? () => window.jarvisDesktop?.playYouTube('') : null },
              { icon: '💻', label: 'Terminal', app: 'terminal' },
              { icon: '📝', label: 'Notepad', app: 'notepad' },
              { icon: '📂', label: 'Files', app: 'explorer' },
              { icon: '🎵', label: 'Spotify', app: 'spotify' },
              { icon: '💻', label: 'VS Code', app: 'vscode' },
              { icon: '🧮', label: 'Calculator', app: 'calculator' },
            ].map(item => (
              <div key={item.label} style={styles.card}
                onClick={() => item.action ? item.action() : openApp(item.app)}>
                <div style={styles.cardIcon}>{item.icon}</div>
                <div style={styles.cardLabel}>{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PC Power Tab */}
      {activeTab === 'pc-power' && isDesktop && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>PC Power Control</div>
          <div style={styles.grid}>
            <div style={{...styles.card, borderColor: 'rgba(255,68,68,0.3)'}}
              onClick={() => pcAction('pcShutdown')}>
              <div style={styles.cardIcon}>{icons.shutdown}</div>
              <div style={styles.cardLabel}>Shutdown</div>
            </div>
            <div style={{...styles.card, borderColor: 'rgba(255,165,0,0.3)'}}
              onClick={() => pcAction('pcRestart')}>
              <div style={styles.cardIcon}>{icons.restart}</div>
              <div style={styles.cardLabel}>Restart</div>
            </div>
            <div style={{...styles.card, borderColor: 'rgba(100,100,255,0.3)'}}
              onClick={() => pcAction('pcSleep')}>
              <div style={styles.cardIcon}>{icons.sleep}</div>
              <div style={styles.cardLabel}>Sleep</div>
            </div>
            <div style={{...styles.card, borderColor: 'rgba(255,215,0,0.3)'}}
              onClick={() => pcAction('pcLock')}>
              <div style={styles.cardIcon}>{icons.lock}</div>
              <div style={styles.cardLabel}>Lock PC</div>
            </div>
            <div style={styles.card} onClick={() => pcAction('pcLogoff')}>
              <div style={styles.cardIcon}>🚪</div>
              <div style={styles.cardLabel}>Log Off</div>
            </div>
            <div style={styles.card} onClick={() => window.jarvisDesktop?.minimizeAll()}>
              <div style={styles.cardIcon}>📉</div>
              <div style={styles.cardLabel}>Hide All Windows</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemControl;
