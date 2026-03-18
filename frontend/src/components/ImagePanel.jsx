import React from 'react'

export default function ImagePanel({ imageUrl, croppedPlate, plateText, onClear }) {
  return (
    <div className="image-panel">
      <div className="panel-section">
        <div className="panel-label">KAMERA GORUNTUSU</div>
        {imageUrl ? (
          <div className="image-wrapper">
            <img src={imageUrl} alt="Arac" className="vehicle-image" />
            {onClear && (
              <button className="image-clear-btn" onClick={onClear} title="Gorseli kaldir">
                &times;
              </button>
            )}
          </div>
        ) : (
          <div className="placeholder">Henuz gorsel yuklenmedi</div>
        )}
      </div>
      {croppedPlate && (
        <div className="panel-section">
          <div className="panel-label">PLAKA BOLGESI</div>
          <div className="plate-crop">
            <img src={`data:image/jpeg;base64,${croppedPlate}`} alt="Plaka" />
            {plateText && <span className="plate-text">{plateText}</span>}
          </div>
        </div>
      )}
    </div>
  )
}
