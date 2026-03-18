import React, { useCallback } from 'react'

export default function UploadZone({ onFileSelect, isProcessing }) {
  const handleDrop = useCallback((e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) onFileSelect(file)
  }, [onFileSelect])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
  }, [])

  return (
    <div
      className="upload-zone"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      <input
        type="file"
        accept="image/*"
        onChange={(e) => e.target.files[0] && onFileSelect(e.target.files[0])}
        id="file-input"
        hidden
      />
      <label htmlFor="file-input" className="upload-label">
        {isProcessing ? 'Isleniyor...' : 'Gorsel yukleyin veya surukleyin'}
      </label>
    </div>
  )
}
