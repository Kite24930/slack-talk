import './ThreadPanel.css';

interface ThreadReply {
  userName: string;
  text: string;
  timestamp: string;
}

interface ThreadPanelProps {
  visible: boolean;
  parentText: string;
  parentAuthor: string;
  replies: ThreadReply[];
  onClose: () => void;
}

export function ThreadPanel({ visible, parentText, parentAuthor, replies, onClose }: ThreadPanelProps) {
  if (!visible) return null;

  return (
    <div className="thread-panel">
      <div className="thread-panel-header">
        <span>スレッド</span>
        <button className="thread-close-btn" onClick={onClose}>✕</button>
      </div>
      <div className="thread-panel-content">
        <div className="thread-parent">
          <span className="thread-parent-author">{parentAuthor}</span>
          <p className="thread-parent-text">{parentText}</p>
        </div>
        <div className="thread-replies">
          {replies.map((reply, i) => (
            <div key={i} className="thread-reply-card">
              <div className="thread-reply-header">
                <span className="thread-reply-author">{reply.userName}</span>
                <span className="thread-reply-time">{reply.timestamp}</span>
              </div>
              <p className="thread-reply-text">{reply.text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
