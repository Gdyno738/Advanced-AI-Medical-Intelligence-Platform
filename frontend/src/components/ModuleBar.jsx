const MODULES = [
  { id: 'chest_xray_pneumonia', icon: '🫁', label: 'Chest X-Ray',  organ: 'Lungs',  active: true  },
  { id: 'brain_tumor',          icon: '🧠', label: 'Brain Tumor',  organ: 'Brain',  active: true  },
  { id: 'skin_cancer',          icon: '🔬', label: 'Skin Cancer',  organ: 'Skin',   active: true  },
  { id: 'retinopathy',          icon: '👁', label: 'Ophthalmology',organ: 'Eye',    active: false },
  { id: 'pathology',            icon: '🧬', label: 'Pathology',    organ: 'Tissue', active: false },
];

export default function ModuleBar({ selectedId, onSelect }) {
  return (
    <div className="module-bar">
      <div className="module-bar-inner">
        <span className="module-label">Modules</span>
        {MODULES.map(m => (
          <div
            key={m.id}
            className={`module-chip ${m.active ? (selectedId === m.id ? 'active' : 'available') : 'soon'}`}
            onClick={() => m.active && onSelect(m.id)}
            title={m.active ? m.organ : 'Coming soon'}
            style={{ cursor: m.active ? 'pointer' : 'default' }}
          >
            <span>{m.icon}</span>
            <span className="chip-dot" />
            <span>{m.label}</span>
            {!m.active && <span className="chip-soon">soon</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
