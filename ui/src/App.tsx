import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { MessageArea } from './components/MessageArea';
import type { Message } from './components/MessageArea';
import { ThreadPanel } from './components/ThreadPanel';
import './styles/global.css';

// Mock data for development
const MOCK_CHANNELS = [
  { id: 'C1', name: 'general', ttsEnabled: true, threads: [{ id: 't1', title: 'デプロイの件' }] },
  { id: 'C2', name: 'random', ttsEnabled: false, threads: [] },
  { id: 'C3', name: 'dev', ttsEnabled: true, threads: [{ id: 't2', title: 'バグ修正PR' }] },
];

const MOCK_MESSAGES: Message[] = [
  { id: 'm1', userName: 'Taro', text: 'お疲れ様です', timestamp: '14:30', priority: 'normal' },
  { id: 'm2', userName: 'Bot', text: 'デプロイ失敗', timestamp: '14:35', priority: 'error' },
  {
    id: 'm3', userName: 'Hanako', text: '確認お願いします', timestamp: '14:31', priority: 'mention',
    threadReplies: [{ userName: 'Taro', text: '送ります', timestamp: '14:32' }],
    threadTotalCount: 3,
  },
];

function App() {
  const [activeChannelId, setActiveChannelId] = useState<string | null>('C1');
  const [threadOpen, setThreadOpen] = useState(false);

  document.documentElement.setAttribute('data-theme', 'dark');

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <Sidebar
        channels={MOCK_CHANNELS}
        activeChannelId={activeChannelId}
        onSelectChannel={setActiveChannelId}
      />
      <MessageArea
        channelName="general"
        messages={MOCK_MESSAGES}
        onOpenThread={() => setThreadOpen(true)}
      />
      <ThreadPanel
        visible={threadOpen}
        parentText="確認お願いします"
        parentAuthor="Hanako"
        replies={[
          { userName: 'Taro', text: '送ります', timestamp: '14:32' },
          { userName: 'Hanako', text: 'ありがとう！', timestamp: '14:33' },
          { userName: 'Taro', text: '完了しました', timestamp: '14:34' },
        ]}
        onClose={() => setThreadOpen(false)}
      />
    </div>
  );
}

export default App;
