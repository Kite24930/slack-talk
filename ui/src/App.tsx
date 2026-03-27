import { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { MessageArea } from './components/MessageArea';
import { Settings } from './components/Settings';
import { useAppStore } from './store/appStore';
import { useWebSocket } from './hooks/useWebSocket';
import './styles/global.css';

function App() {
  const {
    channels,
    activeChannelId,
    messages,
    theme,
    connected,
    setActiveChannel,
    setTheme,
  } = useAppStore();
  const { send } = useWebSocket();
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Request initial data when connected
  useEffect(() => {
    if (connected) {
      send({ type: 'get_channels' });
      send({ type: 'get_settings' });
    }
  }, [connected, send]);

  const activeChannel = channels.find(ch => ch.id === activeChannelId);
  const activeMessages = activeChannelId ? (messages[activeChannelId] || []) : [];

  const handleSelectChannel = (id: string) => {
    setActiveChannel(id);
    send({ type: 'set_active_channel', data: { channel_id: id } });
  };

  // Map channels to sidebar format
  const sidebarChannels = channels.map(ch => ({
    id: ch.id,
    name: ch.name,
    ttsEnabled: ch.ttsEnabled,
    threads: ch.threads || [],
  }));

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <Sidebar
        channels={sidebarChannels}
        activeChannelId={activeChannelId}
        onSelectChannel={handleSelectChannel}
        onOpenSettings={() => setSettingsOpen(true)}
      />
      {settingsOpen ? (
        <Settings
          send={send}
          channels={channels}
          theme={theme}
          setTheme={setTheme}
          onClose={() => setSettingsOpen(false)}
        />
      ) : (
        <MessageArea
          channelName={activeChannel?.name || 'チャンネルを選択'}
          messages={activeMessages}
          onOpenThread={() => {}}
        />
      )}
      {!connected && (
        <div style={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          background: 'var(--accent-red)',
          color: 'white',
          padding: '8px 16px',
          borderRadius: 8,
          fontSize: 13,
        }}>
          バックエンド未接続
        </div>
      )}
    </div>
  );
}

export default App;
