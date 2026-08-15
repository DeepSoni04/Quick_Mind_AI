import { useState } from 'react';
import {
  Settings, Globe, Bell, Shield, Palette, Key, Save, Cpu
} from 'lucide-react';
import './SettingsPage.css';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    llmProvider: 'gemini',
    maxRows: 100,
    queryTimeout: 30,
    autoExecute: false,
    showSQL: true,
    darkMode: true,
    notifications: true,
    hinglishSupport: true,
    voiceInput: true,
    safeMode: true,
    blockDestructive: true,
    logQueries: true,
  });

  const toggle = (key) => setSettings(prev => ({ ...prev, [key]: !prev[key] }));

  return (
    <div className="settings-page">
      <header className="settings-page__header">
        <div>
          <h1><Settings size={24} /> Settings</h1>
          <p>Configure your QueryMind AI preferences</p>
        </div>
        <button className="btn btn-primary"><Save size={16} /> Save Changes</button>
      </header>

      <div className="settings-page__sections">
        {/* AI & Query Settings */}
        <div className="settings-page__section card">
          <div className="settings-page__section-title">
            <Cpu size={18} />
            <h2>AI & Query Settings</h2>
          </div>

          <div className="settings-page__option">
            <div>
              <label>LLM Provider</label>
              <p>Select the AI model for query generation</p>
            </div>
            <select
              className="input-field settings-page__select"
              value={settings.llmProvider}
              onChange={(e) => setSettings(prev => ({ ...prev, llmProvider: e.target.value }))}
            >
              <option value="gemini">Google Gemini</option>
              <option value="gpt">OpenAI GPT-4</option>
              <option value="llama">Meta Llama</option>
            </select>
          </div>

          <div className="settings-page__option">
            <div>
              <label>Max Result Rows</label>
              <p>Maximum number of rows returned per query</p>
            </div>
            <input
              className="input-field settings-page__number"
              type="number"
              value={settings.maxRows}
              onChange={(e) => setSettings(prev => ({ ...prev, maxRows: e.target.value }))}
            />
          </div>

          <div className="settings-page__option">
            <div>
              <label>Query Timeout (seconds)</label>
              <p>Maximum execution time per query</p>
            </div>
            <input
              className="input-field settings-page__number"
              type="number"
              value={settings.queryTimeout}
              onChange={(e) => setSettings(prev => ({ ...prev, queryTimeout: e.target.value }))}
            />
          </div>

          <div className="settings-page__option">
            <div>
              <label>Show Generated SQL</label>
              <p>Display the generated SQL before execution</p>
            </div>
            <button
              className={`settings-page__toggle ${settings.showSQL ? 'settings-page__toggle--on' : ''}`}
              onClick={() => toggle('showSQL')}
            >
              <span className="settings-page__toggle-dot" />
            </button>
          </div>

          <div className="settings-page__option">
            <div>
              <label>Auto-Execute Queries</label>
              <p>Run queries automatically without user approval</p>
            </div>
            <button
              className={`settings-page__toggle ${settings.autoExecute ? 'settings-page__toggle--on' : ''}`}
              onClick={() => toggle('autoExecute')}
            >
              <span className="settings-page__toggle-dot" />
            </button>
          </div>
        </div>

        {/* Language & Input */}
        <div className="settings-page__section card">
          <div className="settings-page__section-title">
            <Globe size={18} />
            <h2>Language & Input</h2>
          </div>

          <div className="settings-page__option">
            <div>
              <label>Hinglish Support</label>
              <p>Enable mixed Hindi-English query processing</p>
            </div>
            <button
              className={`settings-page__toggle ${settings.hinglishSupport ? 'settings-page__toggle--on' : ''}`}
              onClick={() => toggle('hinglishSupport')}
            >
              <span className="settings-page__toggle-dot" />
            </button>
          </div>

          <div className="settings-page__option">
            <div>
              <label>Voice Input</label>
              <p>Enable speech-to-text for query input</p>
            </div>
            <button
              className={`settings-page__toggle ${settings.voiceInput ? 'settings-page__toggle--on' : ''}`}
              onClick={() => toggle('voiceInput')}
            >
              <span className="settings-page__toggle-dot" />
            </button>
          </div>
        </div>

        {/* Security */}
        <div className="settings-page__section card">
          <div className="settings-page__section-title">
            <Shield size={18} />
            <h2>Security</h2>
          </div>

          <div className="settings-page__option">
            <div>
              <label>Safe Mode</label>
              <p>Validate all queries before execution</p>
            </div>
            <button
              className={`settings-page__toggle ${settings.safeMode ? 'settings-page__toggle--on' : ''}`}
              onClick={() => toggle('safeMode')}
            >
              <span className="settings-page__toggle-dot" />
            </button>
          </div>

          <div className="settings-page__option">
            <div>
              <label>Block Destructive Queries</label>
              <p>Prevent DROP, DELETE, TRUNCATE, and ALTER statements</p>
            </div>
            <button
              className={`settings-page__toggle ${settings.blockDestructive ? 'settings-page__toggle--on' : ''}`}
              onClick={() => toggle('blockDestructive')}
            >
              <span className="settings-page__toggle-dot" />
            </button>
          </div>

          <div className="settings-page__option">
            <div>
              <label>Log All Queries</label>
              <p>Store query history for auditing</p>
            </div>
            <button
              className={`settings-page__toggle ${settings.logQueries ? 'settings-page__toggle--on' : ''}`}
              onClick={() => toggle('logQueries')}
            >
              <span className="settings-page__toggle-dot" />
            </button>
          </div>
        </div>

        {/* Appearance */}
        <div className="settings-page__section card">
          <div className="settings-page__section-title">
            <Palette size={18} />
            <h2>Appearance & Notifications</h2>
          </div>

          <div className="settings-page__option">
            <div>
              <label>Dark Mode</label>
              <p>Use dark theme throughout the application</p>
            </div>
            <button
              className={`settings-page__toggle ${settings.darkMode ? 'settings-page__toggle--on' : ''}`}
              onClick={() => toggle('darkMode')}
            >
              <span className="settings-page__toggle-dot" />
            </button>
          </div>

          <div className="settings-page__option">
            <div>
              <label>Notifications</label>
              <p>Receive notifications for query completions and security alerts</p>
            </div>
            <button
              className={`settings-page__toggle ${settings.notifications ? 'settings-page__toggle--on' : ''}`}
              onClick={() => toggle('notifications')}
            >
              <span className="settings-page__toggle-dot" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
