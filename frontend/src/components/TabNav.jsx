export default function TabNav({ activeTab, onChange }) {
  return (
    <nav className="tab-nav">
      <button
        className={`tab-btn ${activeTab === 'predict' ? 'active' : ''}`}
        onClick={() => onChange('predict')}
      >
        Analyze
      </button>
      <button
        className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
        onClick={() => onChange('history')}
      >
        History
      </button>
    </nav>
  );
}
