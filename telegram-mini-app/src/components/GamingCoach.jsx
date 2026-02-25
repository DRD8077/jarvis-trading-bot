/**
 * 🎮 JARVIS Gaming Coach — Real-time BGMI/PUBG Coaching UI
 * ═══════════════════════════════════════════════════════════
 * Full-featured gaming overlay with:
 * - Pro player profile selector (Jonathan, Mortal, Scout, etc.)
 * - Real-time screen sharing + AI analysis
 * - Tactical callouts overlay
 * - Sensitivity settings display
 * - Weapon advice panel
 * - Map strategy view
 * - Performance stats
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import jarvisGameVision from '../services/jarvisGameVision';

// ════════════════════════════════════════
// PRO PLAYER DATA (Client-side mirror)
// ════════════════════════════════════════

const PRO_PLAYERS = {
  jonathan_gaming: {
    name: 'Jonathan Gaming',
    emoji: '🔥',
    style: 'Aggressive Rush • Close Combat King',
    specialty: '4-finger claw, insane reflexes, CQC god',
    color: '#FF4444',
  },
  mortal: {
    name: 'Mortal',
    emoji: '👑',
    style: 'Smart Aggressive • IGL Legend',
    specialty: '3-finger claw, game sense, clutch master',
    color: '#FFD700',
  },
  scout: {
    name: 'Scout',
    emoji: '⚡',
    style: 'Hyper Aggressive • TDM King',
    specialty: '4-finger claw, spray control, M416 beast',
    color: '#00BFFF',
  },
  dynamo_gaming: {
    name: 'Dynamo Gaming',
    emoji: '🎯',
    style: 'Tactical • Sniper Expert',
    specialty: 'Thumb player, calm gameplay, strategic rotations',
    color: '#9B59B6',
  },
  mavi: {
    name: 'Mavi',
    emoji: '🌟',
    style: 'Versatile Fragger • Rising Star',
    specialty: '4-finger claw, versatile weapons, smart pushes',
    color: '#2ECC71',
  },
  zgod: {
    name: 'ZGod',
    emoji: '💀',
    style: 'Support Fragger • Team Player',
    specialty: '4-finger claw, support play, smoke plays',
    color: '#E74C3C',
  },
};

// ════════════════════════════════════════
// COMPONENT STYLES
// ════════════════════════════════════════

const styles = {
  container: {
    background: 'linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%)',
    minHeight: '100vh',
    color: '#fff',
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    position: 'relative',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 20px',
    background: 'rgba(0,0,0,0.4)',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
    backdropFilter: 'blur(10px)',
  },
  headerTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  statusBadge: (isActive) => ({
    fontSize: '12px',
    padding: '4px 10px',
    borderRadius: '12px',
    background: isActive ? 'rgba(46,204,113,0.2)' : 'rgba(255,68,68,0.2)',
    color: isActive ? '#2ecc71' : '#ff4444',
    border: `1px solid ${isActive ? '#2ecc71' : '#ff4444'}`,
  }),
  section: {
    padding: '16px 20px',
  },
  sectionTitle: {
    fontSize: '14px',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    color: '#888',
    marginBottom: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  profileGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '10px',
  },
  profileCard: (isSelected, color) => ({
    padding: '12px 8px',
    borderRadius: '12px',
    background: isSelected ? `${color}22` : 'rgba(255,255,255,0.05)',
    border: `2px solid ${isSelected ? color : 'rgba(255,255,255,0.1)'}`,
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    transform: isSelected ? 'scale(1.02)' : 'scale(1)',
  }),
  profileEmoji: {
    fontSize: '28px',
    marginBottom: '4px',
  },
  profileName: {
    fontSize: '11px',
    fontWeight: '600',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  profileStyle: {
    fontSize: '9px',
    color: '#888',
    marginTop: '2px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  screenShareBtn: (isActive) => ({
    width: '100%',
    padding: '16px',
    borderRadius: '16px',
    border: 'none',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    background: isActive
      ? 'linear-gradient(135deg, #e74c3c, #c0392b)'
      : 'linear-gradient(135deg, #2ecc71, #27ae60)',
    color: '#fff',
    boxShadow: isActive
      ? '0 4px 20px rgba(231,76,60,0.4)'
      : '0 4px 20px rgba(46,204,113,0.4)',
    transition: 'all 0.3s ease',
  }),
  gameStatePanel: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '8px',
  },
  statCard: (color = '#3498db') => ({
    background: 'rgba(255,255,255,0.05)',
    borderRadius: '10px',
    padding: '10px',
    textAlign: 'center',
    border: `1px solid ${color}33`,
  }),
  statValue: {
    fontSize: '20px',
    fontWeight: 'bold',
  },
  statLabel: {
    fontSize: '10px',
    color: '#888',
    textTransform: 'uppercase',
    marginTop: '2px',
  },
  calloutBar: (dangerLevel) => {
    const colors = {
      critical: { bg: 'rgba(231,76,60,0.15)', border: '#e74c3c' },
      high: { bg: 'rgba(230,126,34,0.15)', border: '#e67e22' },
      medium: { bg: 'rgba(241,196,15,0.15)', border: '#f1c40f' },
      safe: { bg: 'rgba(46,204,113,0.15)', border: '#2ecc71' },
    };
    const c = colors[dangerLevel] || colors.safe;
    return {
      padding: '12px 16px',
      margin: '0 20px',
      borderRadius: '12px',
      background: c.bg,
      border: `1px solid ${c.border}`,
      fontSize: '13px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    };
  },
  calloutList: {
    maxHeight: '200px',
    overflowY: 'auto',
    padding: '0 20px',
  },
  calloutItem: {
    padding: '8px 12px',
    margin: '4px 0',
    borderRadius: '8px',
    background: 'rgba(255,255,255,0.03)',
    fontSize: '12px',
    borderLeft: '3px solid #3498db',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  quickAction: {
    padding: '10px 14px',
    borderRadius: '10px',
    border: '1px solid rgba(255,255,255,0.15)',
    background: 'rgba(255,255,255,0.05)',
    color: '#fff',
    fontSize: '12px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    whiteSpace: 'nowrap',
  },
  quickActionsContainer: {
    display: 'flex',
    gap: '8px',
    overflowX: 'auto',
    padding: '0 20px 16px 20px',
    scrollbarWidth: 'none',
    msOverflowStyle: 'none',
  },
  sensitivityPanel: {
    background: 'rgba(255,255,255,0.03)',
    borderRadius: '12px',
    padding: '14px',
    border: '1px solid rgba(255,255,255,0.08)',
  },
  sensRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '6px 0',
    borderBottom: '1px solid rgba(255,255,255,0.05)',
    fontSize: '12px',
  },
  sensLabel: { color: '#aaa' },
  sensValue: { fontWeight: 'bold', color: '#3498db' },
  weaponTip: {
    background: 'rgba(52,152,219,0.1)',
    borderRadius: '12px',
    padding: '14px',
    border: '1px solid rgba(52,152,219,0.2)',
    marginTop: '8px',
  },
  chatInput: {
    display: 'flex',
    gap: '8px',
    padding: '12px 20px',
    background: 'rgba(0,0,0,0.3)',
    borderTop: '1px solid rgba(255,255,255,0.1)',
    position: 'sticky',
    bottom: 0,
  },
  input: {
    flex: 1,
    padding: '12px 16px',
    borderRadius: '12px',
    border: '1px solid rgba(255,255,255,0.15)',
    background: 'rgba(255,255,255,0.05)',
    color: '#fff',
    fontSize: '14px',
    outline: 'none',
  },
  sendBtn: {
    padding: '12px 20px',
    borderRadius: '12px',
    border: 'none',
    background: 'linear-gradient(135deg, #3498db, #2980b9)',
    color: '#fff',
    fontWeight: 'bold',
    cursor: 'pointer',
    fontSize: '14px',
  },
};

// ════════════════════════════════════════
// GAMING COACH COMPONENT
// ════════════════════════════════════════

const GamingCoach = ({ onBack, apiBase }) => {
  const [selectedProfile, setSelectedProfile] = useState('jonathan_gaming');
  const [isSharing, setIsSharing] = useState(false);
  const [gameState, setGameState] = useState({});
  const [callouts, setCallouts] = useState([]);
  const [latestCallout, setLatestCallout] = useState('');
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [showSensitivity, setShowSensitivity] = useState(false);
  const [sensitivity, setSensitivity] = useState(null);
  const [weaponTip, setWeaponTip] = useState(null);
  const [frameCount, setFrameCount] = useState(0);
  const [shareMode, setShareMode] = useState('');
  
  const chatEndRef = useRef(null);
  const base = apiBase || window.API_BASE || 'http://127.0.0.1:8000';

  // Set API base for game vision
  useEffect(() => {
    jarvisGameVision.apiBase = base;
  }, [base]);

  // Register analysis callbacks
  useEffect(() => {
    jarvisGameVision.onAnalysis((analysis) => {
      setGameState(analysis.analysis || {});
      setFrameCount(jarvisGameVision.getFrameCount());

      if (analysis.callouts) {
        setCallouts(prev => [...prev.slice(-20), ...analysis.callouts.map(c => ({
          text: c,
          time: new Date().toLocaleTimeString(),
        }))]);
        setLatestCallout(analysis.callouts[analysis.callouts.length - 1] || '');
      }
    });

    jarvisGameVision.onCallout((text) => {
      setLatestCallout(text);
    });

    return () => {
      jarvisGameVision.onAnalysis(null);
      jarvisGameVision.onCallout(null);
    };
  }, []);

  // ─── Profile Switch ──────────────────
  const handleProfileSwitch = useCallback(async (profileKey) => {
    setSelectedProfile(profileKey);
    jarvisGameVision.gamingProfile = profileKey;
    
    try {
      const res = await fetch(`${base}/api/gaming/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile: profileKey }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.sensitivity) setSensitivity(data.sensitivity);
      }
    } catch (err) {
      // Offline
    }

    setChatMessages(prev => [...prev, {
      role: 'jarvis',
      text: `🎮 Switched to ${PRO_PLAYERS[profileKey]?.name || profileKey} profile! Playing with their sensitivity and style.`,
    }]);
  }, [base]);

  // ─── Screen Share Toggle ──────────────
  const toggleScreenShare = useCallback(async () => {
    if (isSharing) {
      const result = jarvisGameVision.stopScreenCapture();
      setIsSharing(false);
      setShareMode('');
      setChatMessages(prev => [...prev, {
        role: 'jarvis',
        text: `📺 Screen sharing stopped. Analyzed ${result.framesAnalyzed} frames. Good game!`,
      }]);
    } else {
      const result = await jarvisGameVision.startScreenCapture();
      if (result.success) {
        setIsSharing(true);
        setShareMode(result.mode);
        setChatMessages(prev => [...prev, {
          role: 'jarvis',
          text: result.message,
        }]);
      } else {
        setChatMessages(prev => [...prev, {
          role: 'jarvis',
          text: `❌ ${result.error}`,
        }]);
      }
    }
  }, [isSharing]);

  // ─── Quick Actions ──────────────────
  const quickActions = [
    { emoji: '🔫', label: 'M416 Tips', action: () => getWeaponAdvice('M416') },
    { emoji: '💥', label: 'AKM Tips', action: () => getWeaponAdvice('AKM') },
    { emoji: '🎯', label: 'AWM Tips', action: () => getWeaponAdvice('AWM') },
    { emoji: '🗺️', label: 'Erangel', action: () => getMapStrategy('Erangel') },
    { emoji: '🌴', label: 'Sanhok', action: () => getMapStrategy('Sanhok') },
    { emoji: '⚙️', label: 'Sensitivity', action: () => setShowSensitivity(!showSensitivity) },
    { emoji: '🧠', label: 'IQ Tips', action: () => getIQTips() },
    { emoji: '🔊', label: 'Callouts', action: () => getCalloutGuide() },
  ];

  const getWeaponAdvice = async (weapon) => {
    try {
      const res = await fetch(`${base}/api/gaming/weapon`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ weapon, profile: selectedProfile }),
      });
      if (res.ok) {
        const data = await res.json();
        setWeaponTip(data);
        setChatMessages(prev => [...prev, {
          role: 'jarvis',
          text: data.advice || `🔫 ${weapon}: ${data.tip || 'Aim for the head, control your spray!'}`,
        }]);
      }
    } catch (err) {
      setChatMessages(prev => [...prev, {
        role: 'jarvis',
        text: `🔫 ${weapon}: Pull down steadily for spray control. Burst fire at range. Tap fire 100m+.`,
      }]);
    }
  };

  const getMapStrategy = async (map) => {
    try {
      const res = await fetch(`${base}/api/gaming/map`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ map, profile: selectedProfile }),
      });
      if (res.ok) {
        const data = await res.json();
        setChatMessages(prev => [...prev, {
          role: 'jarvis',
          text: data.strategy || `🗺️ ${map}: Rotate early, use vehicles, avoid open fields.`,
        }]);
      }
    } catch (err) {
      setChatMessages(prev => [...prev, {
        role: 'jarvis',
        text: `🗺️ ${map}: Drop safe, loot fast, rotate with zone, hold compound advantage.`,
      }]);
    }
  };

  const getIQTips = () => {
    setChatMessages(prev => [...prev, {
      role: 'jarvis',
      text: `🧠 Pro IQ Tips:\n• Always check map every 5 seconds\n• Pre-aim common angles before peeking\n• Use sound cues — footsteps tell distance & direction\n• Don't fight outside zone after Phase 3\n• Use smokes for revives & rotations\n• Jiggle-peek to bait shots before engaging\n• High ground = advantage, always take it\n• Vehicle rotation in open maps (Erangel/Miramar)\n• Trade kills — if teammate knocked, push immediately\n• Save grenades for final circles`,
    }]);
  };

  const getCalloutGuide = () => {
    setChatMessages(prev => [...prev, {
      role: 'jarvis',
      text: `🔊 BGMI Callouts:\n• "Contact [direction] [distance]!" — Enemy spotted\n• "One knocked!" — Enemy downed\n• "Pushing!" — Moving toward enemy\n• "Rotate!" — Change position\n• "Zone pulling!" — Zone closing in\n• "Nade out!" — Throwing grenade\n• "Smoke!" — Deploying smoke\n• "Revive me!" — Need revive\n• "Hold!" — Stay in position\n• "Flush!" — Finish knocked player`,
    }]);
  };

  // ─── Chat Send ──────────────────
  const handleChatSend = async () => {
    if (!chatInput.trim()) return;
    const msg = chatInput.trim();
    setChatInput('');

    setChatMessages(prev => [...prev, { role: 'user', text: msg }]);

    try {
      const res = await fetch(`${base}/api/gaming/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: msg,
          profile: selectedProfile,
          game_state: gameState,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setChatMessages(prev => [...prev, {
          role: 'jarvis',
          text: data.response || data.message || 'Let me analyze that...',
        }]);
      } else {
        throw new Error('Server error');
      }
    } catch (err) {
      // Offline fallback
      setChatMessages(prev => [...prev, {
        role: 'jarvis',
        text: getOfflineResponse(msg),
      }]);
    }
  };

  const getOfflineResponse = (msg) => {
    const lower = msg.toLowerCase();
    if (lower.includes('sensitivity') || lower.includes('sens'))
      return '⚙️ Tap the Sensitivity button above to see pro player settings!';
    if (lower.includes('m416'))
      return '🔫 M416: Best all-rounder. Use compensator + vertical grip + extended mag. Spray pattern: pull down-left slightly.';
    if (lower.includes('akm'))
      return '🔫 AKM: High damage but hard recoil. Use compensator + half grip. Single-tap at 100m+.';
    if (lower.includes('awm'))
      return '🎯 AWM: One-shot headshot with any helmet. Lead moving targets. Hold breath for accuracy.';
    if (lower.includes('drop') || lower.includes('land') || lower.includes('where'))
      return '🪂 Hot drops: Pochinki, Bootcamp, Paradise Resort. Safe drops: Gatka, Mylta, Ruins.';
    if (lower.includes('play like') || lower.includes('jonathan'))
      return `🔥 Playing like Jonathan: Rush everything, 4-finger claw, always take close-range fights, use M416/AKM, quick peek and pre-fire!`;
    return `🎮 I'm your gaming coach! Ask me about weapons, sensitivity, maps, or strategies. Start screen sharing for real-time coaching!`;
  };

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // ────────────────────────────────────
  // RENDER
  // ────────────────────────────────────

  const currentProfile = PRO_PLAYERS[selectedProfile] || PRO_PLAYERS.jonathan_gaming;
  const dangerLevel = gameState.danger_level || gameState.dangerLevel || 'safe';

  return (
    <div style={styles.container}>
      {/* ══ HEADER ══ */}
      <div style={styles.header}>
        <div style={styles.headerTitle}>
          {onBack && (
            <button 
              onClick={onBack}
              style={{ background: 'none', border: 'none', color: '#fff', fontSize: '20px', cursor: 'pointer', padding: '0 8px 0 0' }}
            >
              ←
            </button>
          )}
          🎮 Gaming Coach
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={styles.statusBadge(isSharing)}>
            {isSharing ? '● LIVE' : '○ OFF'}
          </span>
          {frameCount > 0 && (
            <span style={{ fontSize: '11px', color: '#888' }}>
              {frameCount} frames
            </span>
          )}
        </div>
      </div>

      {/* ══ LIVE CALLOUT BAR ══ */}
      {latestCallout && (
        <div style={{ padding: '8px 20px' }}>
          <div style={styles.calloutBar(dangerLevel)}>
            <span style={{ fontSize: '16px' }}>
              {dangerLevel === 'critical' ? '🚨' : dangerLevel === 'high' ? '⚠️' : dangerLevel === 'medium' ? '⚡' : '✅'}
            </span>
            <span>{latestCallout}</span>
          </div>
        </div>
      )}

      {/* ══ GAME STATE (when sharing) ══ */}
      {isSharing && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>📊 Game State</div>
          <div style={styles.gameStatePanel}>
            <div style={styles.statCard('#e74c3c')}>
              <div style={{ ...styles.statValue, color: '#e74c3c' }}>{gameState.enemies_visible || gameState.enemies || 0}</div>
              <div style={styles.statLabel}>Enemies</div>
            </div>
            <div style={styles.statCard('#2ecc71')}>
              <div style={{ ...styles.statValue, color: '#2ecc71' }}>{gameState.health_percent || gameState.health || '100'}%</div>
              <div style={styles.statLabel}>Health</div>
            </div>
            <div style={styles.statCard('#f39c12')}>
              <div style={{ ...styles.statValue, color: '#f39c12' }}>{gameState.zone_phase || gameState.zone || 0}</div>
              <div style={styles.statLabel}>Zone</div>
            </div>
            <div style={styles.statCard('#9b59b6')}>
              <div style={{ ...styles.statValue, color: '#9b59b6' }}>{gameState.kill_count || gameState.kills || 0}</div>
              <div style={styles.statLabel}>Kills</div>
            </div>
            <div style={styles.statCard('#3498db')}>
              <div style={{ ...styles.statValue, color: '#3498db', fontSize: '14px' }}>{gameState.current_weapon || gameState.weapon || '—'}</div>
              <div style={styles.statLabel}>Weapon</div>
            </div>
            <div style={styles.statCard('#1abc9c')}>
              <div style={{ ...styles.statValue, color: '#1abc9c', fontSize: '14px' }}>{gameState.state || 'idle'}</div>
              <div style={styles.statLabel}>State</div>
            </div>
          </div>
        </div>
      )}

      {/* ══ PRO PLAYER PROFILES ══ */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>👤 Play Like a Pro</div>
        <div style={styles.profileGrid}>
          {Object.entries(PRO_PLAYERS).map(([key, player]) => (
            <div
              key={key}
              style={styles.profileCard(selectedProfile === key, player.color)}
              onClick={() => handleProfileSwitch(key)}
            >
              <div style={styles.profileEmoji}>{player.emoji}</div>
              <div style={styles.profileName}>{player.name}</div>
              <div style={styles.profileStyle}>{player.style.split('•')[0].trim()}</div>
            </div>
          ))}
        </div>
        <div style={{
          marginTop: '8px',
          padding: '8px 12px',
          borderRadius: '8px',
          background: `${currentProfile.color}15`,
          border: `1px solid ${currentProfile.color}33`,
          fontSize: '12px',
          color: '#ccc',
        }}>
          {currentProfile.emoji} <strong>{currentProfile.name}</strong>: {currentProfile.specialty}
        </div>
      </div>

      {/* ══ SCREEN SHARE BUTTON ══ */}
      <div style={{ padding: '0 20px 16px' }}>
        <button style={styles.screenShareBtn(isSharing)} onClick={toggleScreenShare}>
          {isSharing ? (
            <>📺 Stop Screen Sharing</>
          ) : (
            <>🎬 Start Screen Sharing — Get Real-time Coaching!</>
          )}
        </button>
        {shareMode === 'manual' && (
          <div style={{ fontSize: '11px', color: '#888', textAlign: 'center', marginTop: '6px' }}>
            📸 Take screenshots during gameplay — JARVIS will analyze them
          </div>
        )}
      </div>

      {/* ══ QUICK ACTIONS ══ */}
      <div style={styles.quickActionsContainer}>
        {quickActions.map((action, i) => (
          <button key={i} style={styles.quickAction} onClick={action.action}>
            {action.emoji} {action.label}
          </button>
        ))}
      </div>

      {/* ══ SENSITIVITY PANEL ══ */}
      {showSensitivity && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>⚙️ {currentProfile.name} Sensitivity</div>
          <div style={styles.sensitivityPanel}>
            {[
              ['Camera (Free Look)', '95-115%'],
              ['Red Dot / Holo', '55-70%'],
              ['2x Scope', '38-45%'],
              ['3x Scope', '28-35%'],
              ['4x Scope', '18-25%'],
              ['6x Scope', '12-18%'],
              ['8x Scope', '8-12%'],
              ['ADS (Free Look)', '90-110%'],
              ['Gyroscope', 'ON (300-400%)'],
            ].map(([label, value]) => (
              <div key={label} style={styles.sensRow}>
                <span style={styles.sensLabel}>{label}</span>
                <span style={styles.sensValue}>{sensitivity?.[label] || value}</span>
              </div>
            ))}
          </div>
          <div style={{ fontSize: '11px', color: '#888', marginTop: '8px', textAlign: 'center' }}>
            💡 Adjust based on your device — these are reference values from {currentProfile.name}
          </div>
        </div>
      )}

      {/* ══ WEAPON TIP ══ */}
      {weaponTip && (
        <div style={{ padding: '0 20px' }}>
          <div style={styles.weaponTip}>
            <div style={{ fontWeight: 'bold', marginBottom: '6px' }}>
              🔫 {weaponTip.weapon || 'Weapon'} — {weaponTip.category || 'AR'}
            </div>
            <div style={{ fontSize: '12px', color: '#ccc', lineHeight: '1.6' }}>
              {weaponTip.advice || weaponTip.tip || 'Control your spray, aim for the head!'}
            </div>
          </div>
        </div>
      )}

      {/* ══ CALLOUT HISTORY ══ */}
      {callouts.length > 0 && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>📢 Callouts</div>
          <div style={styles.calloutList}>
            {callouts.slice(-10).map((c, i) => (
              <div key={i} style={styles.calloutItem}>
                <span style={{ fontSize: '10px', color: '#666', minWidth: '55px' }}>{c.time}</span>
                <span>{c.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ══ CHAT MESSAGES ══ */}
      {chatMessages.length > 0 && (
        <div style={{ ...styles.section, paddingBottom: '80px' }}>
          <div style={styles.sectionTitle}>💬 Coach Chat</div>
          {chatMessages.slice(-15).map((msg, i) => (
            <div
              key={i}
              style={{
                marginBottom: '8px',
                padding: '10px 14px',
                borderRadius: msg.role === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                background: msg.role === 'user'
                  ? 'rgba(52,152,219,0.15)'
                  : 'rgba(255,255,255,0.05)',
                borderLeft: msg.role === 'jarvis' ? '3px solid #3498db' : 'none',
                borderRight: msg.role === 'user' ? '3px solid #2ecc71' : 'none',
                fontSize: '13px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
              }}
            >
              <div style={{ fontSize: '10px', color: '#888', marginBottom: '4px' }}>
                {msg.role === 'user' ? '👤 You' : '🤖 JARVIS Coach'}
              </div>
              {msg.text}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
      )}

      {/* ══ CHAT INPUT ══ */}
      <div style={styles.chatInput}>
        <input
          style={styles.input}
          placeholder="Ask about weapons, maps, sensitivity..."
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleChatSend()}
        />
        <button style={styles.sendBtn} onClick={handleChatSend}>
          🎯
        </button>
      </div>
    </div>
  );
};

export default GamingCoach;
