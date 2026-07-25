const MODEL_META = {
  chest_xray_pneumonia: { label: 'Chest X-Ray Pneumonia Detector', detail: 'X-Ray · Lungs · DenseNet121' },
  brain_tumor:          { label: 'Brain Tumor MRI Classifier',      detail: 'MRI · Brain · DenseNet121'  },
  skin_cancer:          { label: 'Skin Cancer Detector',            detail: 'Dermoscopy · Skin · DenseNet121' },
};

export default function Header({ apiOnline, selectedModel }) {
  const meta = MODEL_META[selectedModel] ?? { label: 'Multi-Modal Medical AI', detail: 'Select a module below' };
  const statusClass = apiOnline === null ? 'loading' : apiOnline ? 'online' : 'offline';
  const statusText  = apiOnline === null ? 'Connecting' : apiOnline ? 'Online' : 'Offline';

  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="header-brand">
          <div className="header-icon">🏥</div>
          <div>
            <div className="header-name">Advanced AI Medical Intelligence</div>
            <div className="header-tagline">{meta.detail}</div>
          </div>
        </div>
        <div className="header-right">
          <div className="status-pill">
            <span className={`status-dot ${statusClass}`} />
            <span>{statusText}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
