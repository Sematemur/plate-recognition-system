import React, { useState, useCallback, useEffect } from 'react'
import Header from './components/Header'
import ImagePanel from './components/ImagePanel'
import ResultPanel from './components/ResultPanel'
import UploadZone from './components/UploadZone'
import HistoryLog from './components/HistoryLog'
import { recognizeImage } from './api'

function loadState(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function saveState(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch { /* quota exceeded — ignore */ }
}

export default function App() {
  const [imageUrl, setImageUrl] = useState(() => loadState('opet_imageUrl', null))
  const [croppedPlate, setCroppedPlate] = useState(() => loadState('opet_croppedPlate', null))
  const [result, setResult] = useState(() => loadState('opet_result', null))
  const [isProcessing, setIsProcessing] = useState(false)
  const [logs, setLogs] = useState(() => loadState('opet_logs', []))

  useEffect(() => { saveState('opet_result', result) }, [result])
  useEffect(() => { saveState('opet_logs', logs) }, [logs])
  useEffect(() => { saveState('opet_imageUrl', imageUrl) }, [imageUrl])
  useEffect(() => { saveState('opet_croppedPlate', croppedPlate) }, [croppedPlate])

  const handleFileSelect = useCallback(async (file) => {
    setIsProcessing(true)
    setResult(null)
    setCroppedPlate(null)

    const reader = new FileReader()
    reader.onload = () => setImageUrl(reader.result)
    reader.readAsDataURL(file)

    try {
      const data = await recognizeImage(file)
      setResult(data)
      if (!data.error) {
        setLogs((prev) => [data, ...prev])
      }
    } catch {
      setResult({ error: 'service_unavailable' })
    } finally {
      setIsProcessing(false)
    }
  }, [])

  const handleClearImage = useCallback(() => {
    setImageUrl(null)
    setCroppedPlate(null)
    setResult(null)
  }, [])

  const handleVehicleRegistered = useCallback((vehicle) => {
    setResult((prev) => ({
      ...prev,
      is_known: true,
      vehicle,
    }))
  }, [])

  return (
    <div className="app">
      <Header />

      <div className="controls">
        <UploadZone onFileSelect={handleFileSelect} isProcessing={isProcessing} />
      </div>

      <div className="main-content">
        <ImagePanel
          imageUrl={imageUrl}
          croppedPlate={croppedPlate}
          plateText={result?.plate_text}
          onClear={imageUrl ? handleClearImage : undefined}
        />
        <ResultPanel
          result={result}
          onVehicleRegistered={handleVehicleRegistered}
        />
      </div>

      <HistoryLog logs={logs} />
    </div>
  )
}
