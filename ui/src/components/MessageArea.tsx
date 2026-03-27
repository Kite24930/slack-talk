import './MessageArea.css';

export interface Message {
  id: string;
  userName: string;
  text: string;
  timestamp: string;
  priority: 'normal' | 'mention' | 'bot' | 'error';
  threadReplies?: { userName: string; text: string; timestamp: string }[];
  threadTotalCount?: number;
}

interface MessageAreaProps {
  channelName: string;
  messages: Message[];
  onOpenThread: (messageId: string) => void;
}

export function MessageArea({ channelName, messages, onOpenThread }: MessageAreaProps) {
  return (
    <div className="message-area">
      <div className="message-header">
        <span className="message-header-hash">#</span>
        {channelName}
      </div>
      <div className="message-list">
        {messages.map(msg => (
          <div key={msg.id} className={`message-card priority-${msg.priority}`}>
            <div className="message-card-header">
              <span className="message-author">{msg.userName}</span>
              <span className="message-time">{msg.timestamp}</span>
            </div>
            <div className="message-text">{msg.text}</div>
            {msg.threadReplies && msg.threadReplies.length > 0 && (
              <div className="message-thread-preview">
                {msg.threadReplies.map((reply, i) => (
                  <div key={i} className="thread-reply-preview">
                    <span className="reply-author">{reply.userName}</span>
                    <span className="reply-text">{reply.text}</span>
                  </div>
                ))}
                {(msg.threadTotalCount ?? 0) > (msg.threadReplies?.length ?? 0) && (
                  <button
                    className="show-thread-btn"
                    onClick={() => onOpenThread(msg.id)}
                  >
                    スレッドを表示 ({msg.threadTotalCount}件)
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      <VoiceStatusInline />
    </div>
  );
}

function VoiceStatusInline() {
  return (
    <div className="voice-status">
      <span className="voice-icon">🎤</span>
      <span>待機中</span>
    </div>
  );
}
