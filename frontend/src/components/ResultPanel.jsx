import React, { useState, useEffect } from 'react'
import { registerVehicle, updateVehicle, confirmLog } from '../api'

export default function ResultPanel({ result, onVehicleRegistered }) {
  const [form, setForm] = useState({
    plate: result?.plate_text || '',
    fuel_type: 'dizel',
    brand: '',
    model: '',
    color: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [manualEntry, setManualEntry] = useState(false)
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    setForm({
      plate: result?.error ? '' : (result?.plate_text || ''),
      fuel_type: 'dizel',
      brand: '',
      model: '',
      color: '',
    })
    setManualEntry(false)
    setEditing(false)
  }, [result?.plate_text, result?.error])

  if (!result) {
    return (
      <div className="result-panel">
        <div className="panel-label">ARAC BILGISI</div>
        <div className="placeholder">Sonuc bekleniyor...</div>
      </div>
    )
  }

  if (result.error && !manualEntry) {
    return (
      <div className="result-panel">
        <div className="panel-label">ARAC BILGISI</div>
        <div className="result-card error">
          <div className="result-status">Plaka algilanamadi</div>
          <p>Goruntude plaka tespit edilemedi.</p>
          <button
            className="btn btn-primary"
            onClick={() => setManualEntry(true)}
          >
            Elle Bilgi Gir
          </button>
        </div>
      </div>
    )
  }

  if (result.is_known && !editing) {
    const v = result.vehicle
    const startEditing = () => {
      setForm({
        plate: v.plate_display || v.plate_number,
        fuel_type: v.fuel_type || 'dizel',
        brand: v.brand || '',
        model: v.model || '',
        color: v.color || '',
      })
      setEditing(true)
    }
    return (
      <div className="result-panel">
        <div className="panel-label">ARAC BILGISI</div>
        <div className="result-card known">
          <div className="result-card-header">
            <span className="status-badge known">Kayitli Arac</span>
            <button className="btn btn-edit" onClick={startEditing}>Duzenle</button>
          </div>
          <div className="vehicle-info-grid">
            {v.fuel_type && (
              <div className="info-row">
                <span className="info-label">Yakit Turu</span>
                <span className="info-value">{v.fuel_type.charAt(0).toUpperCase() + v.fuel_type.slice(1)}</span>
              </div>
            )}
            {(v.brand || v.model) && (
              <div className="info-row">
                <span className="info-label">Arac</span>
                <span className="info-value">{[v.brand, v.model].filter(Boolean).join(' ')}</span>
              </div>
            )}
            {v.color && (
              <div className="info-row">
                <span className="info-label">Renk</span>
                <span className="info-value">{v.color}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  const isEditing = result.is_known && editing
  const isManual = result.error && manualEntry

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      if (isEditing) {
        const vehicle = await updateVehicle(result.vehicle.id, {
          fuel_type: form.fuel_type,
          brand: form.brand || null,
          model: form.model || null,
          color: form.color || null,
        })
        onVehicleRegistered(vehicle)
        setEditing(false)
      } else {
        const plateNormalized = form.plate.replace(/\s/g, '').toUpperCase()
        if (result.log_id) {
          await confirmLog(result.log_id, form.plate)
        }
        const vehicle = await registerVehicle({
          plate_number: plateNormalized,
          plate_display: form.plate,
          fuel_type: form.fuel_type,
          brand: form.brand || null,
          model: form.model || null,
          color: form.color || null,
        })
        onVehicleRegistered(vehicle)
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  let panelTitle = 'YENI ARAC KAYDI'
  let cardClass = 'unknown'
  let badgeClass = 'unknown'
  let badgeText = 'Kayitsiz Arac'

  if (isEditing) {
    panelTitle = 'ARAC DUZENLEME'
    cardClass = 'known'
    badgeClass = 'known'
    badgeText = 'Duzenleniyor'
  } else if (isManual) {
    panelTitle = 'ELLE ARAC KAYDI'
    cardClass = 'manual'
    badgeClass = 'manual'
    badgeText = 'Elle Giris'
  }

  return (
    <div className="result-panel">
      <div className="panel-label">{panelTitle}</div>
      <div className={`result-card ${cardClass}`}>
        <span className={`status-badge ${badgeClass}`}>{badgeText}</span>
        <form onSubmit={handleSubmit} className="register-form">
          {!isEditing && (
            <label>
              Plaka
              <input value={form.plate} onChange={(e) => setForm({ ...form, plate: e.target.value })} required />
            </label>
          )}
          <label>
            Yakit Tipi
            <select value={form.fuel_type} onChange={(e) => setForm({ ...form, fuel_type: e.target.value })} required>
              <option value="dizel">Dizel</option>
              <option value="benzin">Benzin</option>
              <option value="lpg">LPG</option>
            </select>
          </label>
          <label>
            Marka
            <input value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} />
          </label>
          <label>
            Model
            <input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
          </label>
          <label>
            Renk
            <input value={form.color} onChange={(e) => setForm({ ...form, color: e.target.value })} />
          </label>
          <div className="form-actions">
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Kaydediliyor...' : isEditing ? 'Guncelle' : 'Kaydet'}
            </button>
            {isEditing && (
              <button type="button" className="btn-cancel" onClick={() => setEditing(false)}>
                Iptal
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}
