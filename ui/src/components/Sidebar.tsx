import { useState } from 'react';
import './Sidebar.css';

interface Channel {
  id: string;
  name: string;
  ttsEnabled: boolean;
  threads: { id: string; title: string }[];
}

interface SidebarProps {
  channels: Channel[];
  activeChannelId: string | null;
  onSelectChannel: (id: string) => void;
}

export function Sidebar({ channels, activeChannelId, onSelectChannel }: SidebarProps) {
  const [expandedChannels, setExpandedChannels] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) => {
    setExpandedChannels(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">slack-talk</div>
      <div className="sidebar-channels">
        {channels.map(ch => (
          <div key={ch.id}>
            <div
              className={`channel-item ${activeChannelId === ch.id ? 'active' : ''}`}
              onClick={() => onSelectChannel(ch.id)}
            >
              <span className="channel-hash">#</span>
              <span className="channel-name">{ch.name}</span>
              {ch.threads.length > 0 && (
                <button
                  className="thread-toggle"
                  onClick={(e) => { e.stopPropagation(); toggleExpand(ch.id); }}
                >
                  {expandedChannels.has(ch.id) ? '▼' : '▶'}
                </button>
              )}
            </div>
            {expandedChannels.has(ch.id) && ch.threads.map(t => (
              <div key={t.id} className="thread-item">
                └ {t.title}
              </div>
            ))}
          </div>
        ))}
      </div>
      <div className="sidebar-footer">
        <button className="settings-btn">Settings</button>
      </div>
    </div>
  );
}
