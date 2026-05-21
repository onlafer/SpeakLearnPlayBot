import React from 'react';

interface SettingsProps {
  lang: string;
  onSetLang: (lang: string) => void;
  onBack: () => void;
}

const Settings: React.FC<SettingsProps> = ({ lang, onSetLang, onBack }) => {
  const languages = [
    { code: 'ar', name: '🇸🇦 Arabic' },
    { code: 'zh', name: '🇨🇳 Chinese' },
    { code: 'en', name: '🇬🇧 English' },
    { code: 'fr', name: '🇫🇷 French' },
    { code: 'fa', name: '🇮🇷 Persian' },
    { code: 'es', name: '🇪🇸 Spanish' },
    { code: 'vi', name: '🇻🇳 Vietnamese' },
    { code: 'ja', name: '🇯🇵 Japanese' },
  ];

  return (
    <div className="card">
      <h2>Settings</h2>
      <p>Current Language: {languages.find(l => l.code === lang)?.name || lang}</p>
      
      <div className="button-grid">
        {languages.map((l) => (
          <button 
            key={l.code} 
            onClick={() => onSetLang(l.code)}
            style={lang === l.code ? { border: '2px solid white' } : {}}
          >
            {l.name}
          </button>
        ))}
      </div>
      
      <button onClick={onBack} style={{ marginTop: '2rem', backgroundColor: '#666' }}>
        Back to Menu
      </button>
    </div>
  );
};

export default Settings;
