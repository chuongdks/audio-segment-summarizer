import { useRef, useState } from "react";
import { useSummarizer } from "./hooks/useSummarizer";
import UploadZone from "./components/UploadZone";
import AudioPlayer from "./components/AudioPlayer";
import SummaryView from "./components/SummaryView";
import TranscriptView from "./components/TranscriptView";
import StatusBar from "./components/StatusBar";
import Tabs from "./components/Tabs";
import "./App.css";

const TABS = [
  { id: "summary",    label: "Summary" },
  { id: "transcript", label: "Transcript" },
];

export default function App() {
  const { result, status, error, run, reset } = useSummarizer();
  const audioRef   = useRef(null);  // shared ref to AudioPlayer's seek function
  const transcriptRef = useRef(null);    // exposes scrollToSegment()

  const [audioUrl,     setAudioUrl]     = useState(null);
  const [activeTab,    setActiveTab]    = useState("summary");
  const [currentTime,  setCurrentTime]  = useState(0);

  function handleFile(file) {
    // Create a local object URL so the <audio> element can play the file
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(URL.createObjectURL(file));
    setActiveTab("summary");
    setCurrentTime(0);
    run(file);
  }

  function handleReset() {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null);
    setCurrentTime(0);
    reset();
  }

  /**
   * Called when a timestamp link is clicked (from SummaryView or TranscriptView).
   * 1. Seeks the audio player
   * 2. Switches to transcript tab so the user can see the highlighted segment
   */
  function handleSeek(seconds) {
    audioRef.current?.seekTo(seconds);
    setActiveTab("transcript");
    // currentTime update from AudioPlayer's onTimeUpdate will trigger
    // TranscriptView's scroll automatically via its useEffect
  }

  /**
   * Called on every audio timeupdate tick — passed down to TranscriptView
   * so it can highlight and scroll to the active segment live.
   */
  function handleTimeUpdate(t) {
    setCurrentTime(t);
  }

  const isProcessing = status === "transcribing" || status === "summarizing";
  const showPlayer   = audioUrl !== null;
  const showResult   = status === "done" && result;

  const segments = result?.transcription?.segments ?? [];

  const tabsWithCounts = TABS.map((t) => ({
    ...t,
    count: t.id === "transcript" && segments.length > 0
      ? segments.length
      : null,
  }));

  return (
    <div className="app">
      <header className="app-header">
        <span className="app-logo">⬤ REC</span>
        <h1 className="app-title">Meeting Summarizer</h1>
        {showResult && (
          <button className="app-reset" onClick={handleReset}>
            New recording
          </button>
        )}
      </header>

      <main className="app-main">
        {/* Upload zone */}
        {!isProcessing && !showResult && (
          <UploadZone onFile={handleFile} />
        )}

        {/* Status / error */}
        {(isProcessing || status === "error") && (
          <StatusBar status={status} error={error} onRetry={handleReset} />
        )}

        {/* Audio player — pinned above tabs, always visible once loaded */}
        {showPlayer && (
          <AudioPlayer
            ref={audioRef}
            src={audioUrl}
            onTimeUpdate={handleTimeUpdate}
          />
        )}

        {/* Tabs + content — only shown once result is ready */}
        {showResult && (
          <>
            <Tabs
              tabs={tabsWithCounts}
              active={activeTab}
              onChange={setActiveTab}
            />

            <div className="app-tab-content">
              {activeTab === "summary" && (
                <SummaryView result={result} onSeek={handleSeek} />
              )}
              {activeTab === "transcript" && (
                <TranscriptView
                  ref={transcriptRef}
                  segments={segments}
                  currentTime={currentTime}
                  onSeek={handleSeek}
                />
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
