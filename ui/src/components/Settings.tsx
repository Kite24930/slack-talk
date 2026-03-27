import { useState } from 'react';
import './Settings.css';

interface Channel {
  id: string;
  name: string;
  ttsEnabled: boolean;
}

interface SettingsProps {
  send: (msg: Record<string, unknown>) => void;
  channels: Channel[];
  theme: string;
  setTheme: (theme: string) => void;
  onClose: () => void;
}

type TabId = 'slack' | 'channels' | 'voice' | 'display';

const TABS: { id: TabId; label: string }[] = [
  { id: 'slack', label: 'Slack接続' },
  { id: 'channels', label: 'チャンネル設定' },
  { id: 'voice', label: '音声設定' },
  { id: 'display', label: '表示設定' },
];

export function Settings({ send, channels, theme, setTheme, onClose }: SettingsProps) {
  const [activeTab, setActiveTab] = useState<TabId>('slack');
  const [volume, setVolume] = useState(0.8);
  const [flowMatchingSteps, setFlowMatchingSteps] = useState(16);
  const [wakeword, setWakeword] = useState('OK Slack');
  const [silenceThreshold, setSilenceThreshold] = useState(2.0);
  const [threadPreviewCount, setThreadPreviewCount] = useState(3);

  const handleToggleTts = (channel: Channel) => {
    send({
      type: 'toggle_tts',
      data: {
        channel_id: channel.id,
        channel_name: channel.name,
        enabled: !channel.ttsEnabled,
      },
    });
  };

  const handleVolumeChange = (value: number) => {
    setVolume(value);
    send({ type: 'update_setting', data: { key: 'volume', value } });
  };

  const handleFlowMatchingStepsChange = (value: number) => {
    setFlowMatchingSteps(value);
    send({ type: 'update_setting', data: { key: 'flow_matching_steps', value } });
  };

  const handleWakewordChange = (value: string) => {
    setWakeword(value);
    send({ type: 'update_setting', data: { key: 'wakeword', value } });
  };

  const handleSilenceThresholdChange = (value: number) => {
    setSilenceThreshold(value);
    send({ type: 'update_setting', data: { key: 'silence_threshold_seconds', value } });
  };

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme);
    send({ type: 'update_setting', data: { key: 'theme', value: newTheme } });
  };

  const handleThreadPreviewCountChange = (value: number) => {
    setThreadPreviewCount(value);
    send({ type: 'update_setting', data: { key: 'thread_preview_count', value } });
  };

  const renderSlackTab = () => (
    <div className="settings-section">
      <h3>Slack App セットアップガイド</h3>
      <ol className="guide-steps">
        <li className="guide-step">
          <span className="guide-step-number">1</span>
          <span className="guide-step-text">
            <a href="https://api.slack.com/apps" target="_blank" rel="noreferrer">
              https://api.slack.com/apps
            </a> にアクセス
          </span>
        </li>
        <li className="guide-step">
          <span className="guide-step-number">2</span>
          <span className="guide-step-text">
            &quot;Create New App&quot; → &quot;From scratch&quot; を選択
          </span>
        </li>
        <li className="guide-step">
          <span className="guide-step-number">3</span>
          <span className="guide-step-text">
            App名とワークスペースを選択
          </span>
        </li>
        <li className="guide-step">
          <span className="guide-step-number">4</span>
          <span className="guide-step-text">
            &quot;OAuth &amp; Permissions&quot; → Bot Token Scopes に以下を追加:
            <br />
            <code>channels:history</code> <code>channels:read</code> <code>chat:write</code> <code>users:read</code>
          </span>
        </li>
        <li className="guide-step">
          <span className="guide-step-number">5</span>
          <span className="guide-step-text">
            &quot;Install to Workspace&quot; → Bot Token (<code>xoxb-</code>) をコピー
          </span>
        </li>
        <li className="guide-step">
          <span className="guide-step-number">6</span>
          <span className="guide-step-text">
            &quot;Socket Mode&quot; を有効化 → App-Level Token (<code>xapp-</code>) を生成
          </span>
        </li>
      </ol>
    </div>
  );

  const renderChannelsTab = () => (
    <div className="settings-section">
      <h3>チャンネル読み上げ設定</h3>
      {channels.length === 0 ? (
        <div className="settings-empty">
          チャンネルが見つかりません。Slackに接続してください。
        </div>
      ) : (
        channels.map(ch => (
          <div key={ch.id} className="channel-setting-item">
            <span className="channel-setting-name">
              <span className="channel-setting-hash">#</span>
              {ch.name}
            </span>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={ch.ttsEnabled}
                onChange={() => handleToggleTts(ch)}
              />
              <span className="toggle-slider" />
            </label>
          </div>
        ))
      )}
    </div>
  );

  const renderVoiceTab = () => (
    <div className="settings-section">
      <h3>音声設定</h3>

      <div className="setting-row">
        <div>
          <div className="setting-label">音量</div>
          <div className="setting-description">読み上げ音声の音量 (0.0 - 1.0)</div>
        </div>
        <div className="setting-control">
          <input
            type="range"
            className="settings-input-range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            onChange={e => handleVolumeChange(parseFloat(e.target.value))}
          />
          <span className="setting-value">{volume.toFixed(1)}</span>
        </div>
      </div>

      <div className="setting-row">
        <div>
          <div className="setting-label">Flow Matching Steps</div>
          <div className="setting-description">TTS生成品質 (1 - 50, 大きいほど高品質)</div>
        </div>
        <div className="setting-control">
          <input
            type="range"
            className="settings-input-range"
            min="1"
            max="50"
            step="1"
            value={flowMatchingSteps}
            onChange={e => handleFlowMatchingStepsChange(parseInt(e.target.value, 10))}
          />
          <span className="setting-value">{flowMatchingSteps}</span>
        </div>
      </div>

      <div className="setting-row">
        <div>
          <div className="setting-label">ウェイクワード</div>
          <div className="setting-description">音声送信を開始するキーワード</div>
        </div>
        <div className="setting-control">
          <input
            type="text"
            className="settings-input-text"
            value={wakeword}
            onChange={e => handleWakewordChange(e.target.value)}
          />
        </div>
      </div>

      <div className="setting-row">
        <div>
          <div className="setting-label">無音検出しきい値</div>
          <div className="setting-description">録音停止までの無音秒数 (0.5 - 5.0)</div>
        </div>
        <div className="setting-control">
          <input
            type="range"
            className="settings-input-range"
            min="0.5"
            max="5"
            step="0.5"
            value={silenceThreshold}
            onChange={e => handleSilenceThresholdChange(parseFloat(e.target.value))}
          />
          <span className="setting-value">{silenceThreshold.toFixed(1)}s</span>
        </div>
      </div>
    </div>
  );

  const renderDisplayTab = () => (
    <div className="settings-section">
      <h3>表示設定</h3>

      <div className="setting-row">
        <div>
          <div className="setting-label">テーマ</div>
          <div className="setting-description">UIの配色テーマを切り替え</div>
        </div>
        <div className="setting-control">
          <div className="theme-toggle-group">
            <button
              className={`theme-toggle-btn ${theme === 'dark' ? 'active' : ''}`}
              onClick={() => handleThemeChange('dark')}
            >
              Dark
            </button>
            <button
              className={`theme-toggle-btn ${theme === 'light' ? 'active' : ''}`}
              onClick={() => handleThemeChange('light')}
            >
              Light
            </button>
          </div>
        </div>
      </div>

      <div className="setting-row">
        <div>
          <div className="setting-label">スレッドプレビュー数</div>
          <div className="setting-description">サイドバーに表示するスレッド返信数 (0 - 10)</div>
        </div>
        <div className="setting-control">
          <input
            type="range"
            className="settings-input-range"
            min="0"
            max="10"
            step="1"
            value={threadPreviewCount}
            onChange={e => handleThreadPreviewCountChange(parseInt(e.target.value, 10))}
          />
          <span className="setting-value">{threadPreviewCount}</span>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'slack':
        return renderSlackTab();
      case 'channels':
        return renderChannelsTab();
      case 'voice':
        return renderVoiceTab();
      case 'display':
        return renderDisplayTab();
    }
  };

  return (
    <div className="settings-panel">
      <div className="settings-header">
        <h2>Settings</h2>
        <button className="settings-close-btn" onClick={onClose}>
          ×
        </button>
      </div>
      <div className="settings-tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`settings-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="settings-content">
        {renderTabContent()}
      </div>
    </div>
  );
}
