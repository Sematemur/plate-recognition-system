import React from 'react'

export default function HistoryLog({ logs }) {
  if (!logs.length) {
    return (
      <div className="history-log">
        <div className="panel-label">TARAMA GECMISI</div>
        <p className="placeholder">Henuz tarama yapilmadi</p>
      </div>
    )
  }

  const formatDate = (vehicle) => {
    if (!vehicle?.created_at) return '-'
    return new Date(vehicle.created_at).toLocaleDateString('tr-TR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="history-log">
      <div className="panel-label">TARAMA GECMISI</div>
      <table>
        <thead>
          <tr>
            <th>Plaka</th>
            <th>Durum</th>
            <th>Kayit Tarihi</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.log_id || log.id}>
              <td>{log.plate_text || log.plate_detected}</td>
              <td>
                <span className={`badge ${log.is_known ? 'known' : 'unknown'}`}>
                  {log.is_known ? 'Kayitli' : 'Yeni'}
                </span>
              </td>
              <td>{log.is_known ? formatDate(log.vehicle) : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
