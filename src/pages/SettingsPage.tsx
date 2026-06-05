import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { DEFAULT_SETTINGS, loadSettings, saveSettings, type Settings } from "../lib/settings";
import { getLLM } from "../workflow/llm";
import { Header } from "../components/Header";

export function SettingsPage() {
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState(loadSettings().apiKey);
  const [baseUrl, setBaseUrl] = useState(loadSettings().baseUrl);
  const [modelName, setModelName] = useState(loadSettings().modelName);
  const [showKey, setShowKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  function handleSave(e: FormEvent) {
    e.preventDefault();
    const s: Settings = { apiKey: apiKey.trim(), baseUrl: baseUrl.trim(), modelName: modelName.trim() };
    saveSettings(s);
    navigate("/");
  }

  async function handleTest() {
    setTesting(true);
    setTestResult(null);
    try {
      saveSettings({ apiKey: apiKey.trim(), baseUrl: baseUrl.trim(), modelName: modelName.trim() });
      const llm = getLLM();
      await llm.invoke([{ role: "user", content: "hi" }]);
      setTestResult("✓ 连接成功");
    } catch (err) {
      setTestResult(`✗ 失败: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setTesting(false);
    }
  }

  function handleReset() {
    setApiKey(DEFAULT_SETTINGS.apiKey);
    setBaseUrl(DEFAULT_SETTINGS.baseUrl);
    setModelName(DEFAULT_SETTINGS.modelName);
  }

  return (
    <div className="container">
      <Header title="LLM 连接设置" subtitle="配置 API Key、BaseURL 与模型名（存于浏览器 localStorage）" />

      <form className="form-section" onSubmit={handleSave}>
        <div className="form-group">
          <label htmlFor="apiKey">API Key</label>
          <div className="input-with-toggle">
            <input
              type={showKey ? "text" : "password"}
              id="apiKey"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              autoComplete="off"
            />
            <button
              type="button"
              className="icon-btn"
              onClick={() => setShowKey((s) => !s)}
            >
              {showKey ? "隐藏" : "显示"}
            </button>
          </div>
          <div className="field-help">请使用额度受限的 Key，避免被盗刷</div>
        </div>

        <div className="form-group">
          <label htmlFor="baseUrl">Base URL</label>
          <input
            type="url"
            id="baseUrl"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder={DEFAULT_SETTINGS.baseUrl}
          />
        </div>

        <div className="form-group">
          <label htmlFor="modelName">模型名</label>
          <input
            type="text"
            id="modelName"
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
            placeholder={DEFAULT_SETTINGS.modelName}
          />
        </div>

        <div className="btn-row">
          <button type="submit" className="btn-submit">保存</button>
          <button type="button" className="btn-submit" onClick={handleTest} disabled={testing || !apiKey}>
            {testing ? "测试中..." : "测试连接"}
          </button>
        </div>

        <div className="btn-row" style={{ marginTop: 12 }}>
          <button type="button" className="btn-submit" onClick={handleReset}>恢复默认</button>
        </div>

        {testResult && (
          <div className="field-help" style={{ marginTop: 12, fontSize: 14 }}>
            {testResult}
          </div>
        )}
      </form>
    </div>
  );
}
