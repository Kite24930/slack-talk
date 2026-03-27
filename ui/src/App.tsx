import { useEffect } from 'react';
import './styles/global.css';

function App() {
  useEffect(() => {
    // Default theme
    document.documentElement.setAttribute('data-theme', 'dark');
  }, []);

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <aside style={{
        width: 240,
        backgroundColor: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-color)',
        padding: 16,
        color: 'var(--text-primary)',
      }}>
        Sidebar
      </aside>
      <main style={{
        flex: 1,
        backgroundColor: 'var(--bg-primary)',
        padding: 16,
      }}>
        Messages
      </main>
    </div>
  );
}

export default App;
