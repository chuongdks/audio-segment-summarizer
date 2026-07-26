import { useRef, useState } from "react";
import { useSummarizer } from "./hooks/useSummarizer";
import UploadZone from "./components/UploadZone";
import AudioPlayer from "./components/AudioPlayer";
import SummaryView from "./components/SummaryView";
import StatusBar from "./components/StatusBar";
import "./App.css";

export default function App() {
  const { result, status, error, run, reset } = useSummarizer();
  const audioRef = useRef(null);           // shared ref to AudioPlayer's seek function
  const [audioUrl, setAudioUrl] = useState(null);

  function handleFile(file) {
    // Create a local object URL so the <audio> element can play the file
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(URL.createObjectURL(file));
    run(file);
  }

  function handleReset() {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null);
    reset();
  }

  // Seek the audio player to a timestamp (called from SummaryView timestamp links)
  function seekTo(seconds) {
    audioRef.current?.seekTo(seconds);
  }

  const isProcessing = status === "transcribing" || status === "summarizing";
  const showPlayer = audioUrl !== null;
  const showSummary = status === "done" && result;

  return (
    <div className="app">
      <header className="app-header">
        <span className="app-logo">⬤ REC</span>
        <h1 className="app-title">Meeting Summarizer</h1>
        {showSummary && (
          <button className="app-reset" onClick={handleReset}>
            New recording
          </button>
        )}
      </header>

      <main className="app-main">
        {/* Upload zone — always visible until processing starts */}
        {!isProcessing && !showSummary && (
          <UploadZone onFile={handleFile} />
        )}

        {/* Status / error feedback */}
        {(isProcessing || status === "error") && (
          <StatusBar status={status} error={error} onRetry={handleReset} />
        )}

        {/* Audio player — visible once a file is loaded */}
        {showPlayer && (
          <AudioPlayer ref={audioRef} src={audioUrl} />
        )}

        {/* Summary — visible once processing is done */}
        {showSummary && (
          <SummaryView result={result} onSeek={seekTo} />
        )}
      </main>
    </div>
  );
}
