import React from 'react'

export default function FeedControls({ isRunning, onStart, onPause }) {
  return (
    <div className="feed-controls">
      {isRunning ? (
        <button onClick={onPause} className="btn btn-warning">⏸ Durdur</button>
      ) : (
        <button onClick={onStart} className="btn btn-primary">▶ Canli Besleme Baslat</button>
      )}
    </div>
  )
}
