import { useState, useEffect } from "react";
import { Settings, X, Save, RotateCcw } from "lucide-react";
import "./SettingsDrawer.css";

const API_BASE = "/api";

const WHISPER_MODELS  = ["tiny", "base", "medium", "large-v3"];
const WHISPER_DEVICES = ["cpu", "cuda"];

export default function SettingsDrawer() {
  const [open,    setOpen]    = useState(false);
  const [config,  setConfig]  = useState(null);
  const [draft,   setDraft]   = useState(null);   // edited but unsaved values
  const [saving,  setSaving]  = useState(false);
  const [saved,   setSaved]   = useState(false);
  const [error,   setError]   = useState(null);

  // Load config from backend when drawer opens
  useEffect(() => {
    if (!open) return;
    fetch(`${API_BASE}/config`)
      .then((r) => r.json())
      .then((data) => {
        setConfig(data);
        setDraft(data);
        setError(null);
      })
      .catch(() => setError("Could not load config from backend."));
  }, [open]);

  function handleChange(key, value) {
    setDraft((d) => ({ ...d, [key]: value }));
    setSaved(false);
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/config`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draft),
      });
      if (!res.ok) throw new Error(await res.text());
      const updated = await res.json();
      setConfig(updated);
      setDraft(updated);
      setSaved(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    setDraft(config);   // revert draft to last saved config
    setSaved(false);
    setError(null);
  }

  const isDirty = draft && config &&
    JSON.stringify(draft) !== JSON.stringify(config);

  return (
    <>
      {/* Gear button in header */}
      <button
        className="settings-trigger"
        onClick={() => setOpen(true)}
        aria-label="Open settings"
      >
        <Settings size={15} />
      </button>

      {/* Backdrop */}
      {open && (
        <div className="settings-backdrop" onClick={() => setOpen(false)} />
      )}

      {/* Drawer */}
      <div className={`settings-drawer ${open ? "settings-drawer--open" : ""}`}>
        <div className="settings-drawer__header">
          <h2 className="settings-drawer__title">Settings</h2>
          <button
            className="settings-drawer__close"
            onClick={() => setOpen(false)}
            aria-label="Close settings"
          >
            <X size={16} />
          </button>
        </div>

        {error && (
          <div className="settings-error">{error}</div>
        )}

        {draft && (
          <div className="settings-body">

            {/* ── Whisper ──────────────────────────────────────────────── */}
            <section className="settings-section">
              <h3 className="settings-section__title">Transcription</h3>

              <div className="settings-field">
                <label className="settings-label">
                  Whisper model
                  <span className="settings-hint">
                    larger = more accurate, slower
                  </span>
                </label>
                <div className="settings-radio-group">
                  {WHISPER_MODELS.map((m) => (
                    <label key={m} className="settings-radio">
                      <input
                        type="radio"
                        name="whisper_model"
                        value={m}
                        checked={draft.whisper_model === m}
                        onChange={() => handleChange("whisper_model", m)}
                      />
                      <span className="settings-radio__label">{m}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="settings-field">
                <label className="settings-label">
                  Device
                  <span className="settings-hint">
                    cuda requires an Nvidia GPU
                  </span>
                </label>
                <div className="settings-radio-group">
                  {WHISPER_DEVICES.map((d) => (
                    <label key={d} className="settings-radio">
                      <input
                        type="radio"
                        name="whisper_device"
                        value={d}
                        checked={draft.whisper_device === d}
                        onChange={() => handleChange("whisper_device", d)}
                      />
                      <span className="settings-radio__label">{d}</span>
                    </label>
                  ))}
                </div>
              </div>
            </section>

            {/* ── Ollama ───────────────────────────────────────────────── */}
            <section className="settings-section">
              <h3 className="settings-section__title">Summarization</h3>

              <div className="settings-field">
                <label className="settings-label" htmlFor="ollama_model">
                  Ollama model
                  <span className="settings-hint">
                    must be pulled via ollama pull
                  </span>
                </label>
                <input
                  id="ollama_model"
                  className="settings-input"
                  type="text"
                  value={draft.ollama_model}
                  onChange={(e) => handleChange("ollama_model", e.target.value)}
                  placeholder="e.g. llama3.1:8b"
                />
              </div>

              <div className="settings-field">
                <label className="settings-label" htmlFor="ollama_timeout">
                  Timeout (seconds)
                  <span className="settings-hint">
                    increase for long meetings
                  </span>
                </label>
                <input
                  id="ollama_timeout"
                  className="settings-input settings-input--short"
                  type="number"
                  min={30}
                  max={1200}
                  value={draft.ollama_timeout}
                  onChange={(e) => handleChange("ollama_timeout", Number(e.target.value))}
                />
              </div>

              <div className="settings-field">
                <label className="settings-label" htmlFor="max_segments">
                  Max segments
                  <span className="settings-hint">
                    ~300 covers 30-40 min of audio
                  </span>
                </label>
                <input
                  id="max_segments"
                  className="settings-input settings-input--short"
                  type="number"
                  min={50}
                  max={2000}
                  value={draft.max_segments}
                  onChange={(e) => handleChange("max_segments", Number(e.target.value))}
                />
              </div>
            </section>

            {/* ── Note ─────────────────────────────────────────────────── */}
            <p className="settings-note">
              Changes apply for this session only. Edit <code>backend/.env</code> to make them permanent.
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="settings-drawer__footer">
          <button
            className="settings-btn settings-btn--ghost"
            onClick={handleReset}
            disabled={!isDirty}
          >
            <RotateCcw size={13} />
            Revert
          </button>
          <button
            className="settings-btn settings-btn--primary"
            onClick={handleSave}
            disabled={!isDirty || saving}
          >
            <Save size={13} />
            {saving ? "Saving…" : saved ? "Saved ✓" : "Apply"}
          </button>
        </div>
      </div>
    </>
  );
}
