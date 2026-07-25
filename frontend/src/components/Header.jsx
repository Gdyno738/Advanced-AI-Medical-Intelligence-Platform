export default function Header({ apiOnline }) {
  const statusClass = apiOnline === null ? 'loading' : apiOnline ? 'online' : 'offline';
  const statusText  = apiOnline === null ? 'Connecting' : apiOnline ? 'Online' : 'Offline';

  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="header-brand">
          <div className="header-icon">🏥</div>
          <div>
            <div className="header-name">Advanced AI Medical Intelligence Platform</div>
            <div className="header-tagline">Deep Learning Diagnostic System</div>
          </div>
        </div>
        <div className="header-right">
        </div>
      </div>
    </header>
  );
}
