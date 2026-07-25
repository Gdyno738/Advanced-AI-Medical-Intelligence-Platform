import { useState, useEffect, useCallback } from 'react';
import { checkHealth } from './api';
import Header    from './components/Header';
import ModuleBar from './components/ModuleBar';
import TabNav    from './components/TabNav';
import PredictTab from './components/PredictTab';
import HistoryTab from './components/HistoryTab';

export default function App() {
  const [activeTab,    setActiveTab]    = useState('predict');
  const [apiOnline,    setApiOnline]    = useState(null);
  const [activeModel,  setActiveModel]  = useState(null);
  const [selectedModel,setSelectedModel]= useState('chest_xray_pneumonia');

  const pollHealth = useCallback(async () => {
    const h = await checkHealth();
    if (h && h.status === 'healthy') {
      setApiOnline(true);
      setActiveModel(h.active_model ?? null);
    } else {
      setApiOnline(!!h);
      setActiveModel(null);
    }
  }, []);

  useEffect(() => {
    pollHealth();
    const t = setInterval(pollHealth, 15000);
    return () => clearInterval(t);
  }, [pollHealth]);

  return (
    <div className="app-wrap">
      <Header    apiOnline={apiOnline} selectedModel={selectedModel} />
      <ModuleBar selectedId={selectedModel} onSelect={setSelectedModel} />

      <main className="page-body">
        <div className="app-container">
          <TabNav activeTab={activeTab} onChange={setActiveTab} />
          {activeTab === 'predict' && (
            <PredictTab
              apiOnline={apiOnline}
              modelId={selectedModel}
            />
          )}
          {activeTab === 'history' && <HistoryTab />}
        </div>
      </main>

      <footer className="app-footer">
        Advanced AI Medical Intelligence Platform · For research and educational purposes only
      </footer>
    </div>
  );
}
