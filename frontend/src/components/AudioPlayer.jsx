import { useRef, useState, useImperativeHandle, forwardRef } from "react";
import { Play, Pause } from "lucide-react";
import "./AudioPlayer.css";

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const AudioPlayer = forwardRef(function AudioPlayer({ src, onTimeUpdate }, ref) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);

  // Expose seekTo() so App.jsx can call it from SummaryView timestamp clicks
  useImperativeHandle(ref, () => ({
    seekTo(seconds) {
      if (!audioRef.current) return;
      audioRef.current.currentTime = seconds;
      audioRef.current.play();
      setPlaying(true);
    },
  }));

  function togglePlay() {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setPlaying(!playing);
  }

  function handleScrub(e) {
    const val = Number(e.target.value);
    if (audioRef.current) audioRef.current.currentTime = val;
    setCurrent(val);
  }

  function handleTimeUpdate(e) {
    const t = e.target.currentTime;
    setCurrent(t);
    onTimeUpdate?.(t);   // bubble up to App so TranscriptView can highlight
  }

  const progress = duration ? (current / duration) * 100 : 0;

  return (
    <div className="audio-player">
      <audio
        ref={audioRef}
        src={src}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={(e) => setDuration(e.target.duration)}
        onEnded={() => setPlaying(false)}
      />

      <button
        className="audio-player__play"
        onClick={togglePlay}
        aria-label={playing ? "Pause" : "Play"}
      >
        {playing ? <Pause size={16} /> : <Play size={16} />}
      </button>

      <div className="audio-player__scrubber">
        <input
          type="range"
          min={0}
          max={duration || 0}
          step={0.1}
          value={current}
          onChange={handleScrub}
          className="audio-player__range"
          style={{ "--progress": `${progress}%` }}
          aria-label="Seek"
        />
      </div>

      <span className="audio-player__time">
        <span className="audio-player__current">{formatTime(current)}</span>
        <span className="audio-player__sep"> / </span>
        <span className="audio-player__duration">{formatTime(duration)}</span>
      </span>
    </div>
  );
});

export default AudioPlayer;
