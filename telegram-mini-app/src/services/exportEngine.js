/**
 * 📊 JARVIS Portfolio Export Engine (CSV + PDF)
 * ══════════════════════════════════════════════
 * - Export portfolio to CSV
 * - Export trade journal to CSV
 * - Generate PDF reports (canvas-based)
 * - P&L summary, holdings breakdown
 * - Date range filtering
 * - Auto-download on mobile
 */

class PortfolioExportEngine {
  /**
   * Export data as CSV file
   * @param {Array<object>} data - Array of objects
   * @param {string} filename - e.g., 'portfolio_2024.csv'
   * @param {object} opts - { columns: [{key, label}] }
   */
  exportCSV(data, filename = 'jarvis_export.csv', opts = {}) {
    if (!data?.length) {
      console.warn('[Export] No data to export')
      return false
    }

    const columns = opts.columns || Object.keys(data[0]).map(k => ({ key: k, label: k }))

    // Header row
    let csv = columns.map(c => `"${c.label}"`).join(',') + '\n'

    // Data rows
    for (const row of data) {
      const values = columns.map(c => {
        let val = row[c.key]
        if (val === null || val === undefined) val = ''
        if (typeof val === 'object') val = JSON.stringify(val)
        // Escape double quotes
        val = String(val).replace(/"/g, '""')
        return `"${val}"`
      })
      csv += values.join(',') + '\n'
    }

    this._download(csv, filename, 'text/csv;charset=utf-8;')
    return true
  }

  /**
   * Export portfolio holdings
   */
  exportPortfolio(holdings) {
    if (!holdings?.length) return false

    const columns = [
      { key: 'symbol', label: 'Symbol' },
      { key: 'name', label: 'Name' },
      { key: 'quantity', label: 'Quantity' },
      { key: 'avg_price', label: 'Avg Price' },
      { key: 'current_price', label: 'Current Price' },
      { key: 'pnl', label: 'P&L' },
      { key: 'pnl_pct', label: 'P&L %' },
      { key: 'value', label: 'Total Value' },
      { key: 'exchange', label: 'Exchange' },
    ]

    const dateStr = new Date().toISOString().split('T')[0]
    return this.exportCSV(holdings, `jarvis_portfolio_${dateStr}.csv`, { columns })
  }

  /**
   * Export trade journal / transaction history
   */
  exportTradeJournal(trades) {
    if (!trades?.length) return false

    const columns = [
      { key: 'date', label: 'Date' },
      { key: 'time', label: 'Time' },
      { key: 'symbol', label: 'Symbol' },
      { key: 'side', label: 'Side' },
      { key: 'type', label: 'Type' },
      { key: 'quantity', label: 'Quantity' },
      { key: 'price', label: 'Price' },
      { key: 'total', label: 'Total' },
      { key: 'fee', label: 'Fee' },
      { key: 'pnl', label: 'Realized P&L' },
      { key: 'exchange', label: 'Exchange' },
      { key: 'strategy', label: 'Strategy' },
      { key: 'notes', label: 'Notes' },
    ]

    const dateStr = new Date().toISOString().split('T')[0]
    return this.exportCSV(trades, `jarvis_trades_${dateStr}.csv`, { columns })
  }

  /**
   * Export signals history
   */
  exportSignals(signals) {
    if (!signals?.length) return false

    const columns = [
      { key: 'timestamp', label: 'Time' },
      { key: 'symbol', label: 'Symbol' },
      { key: 'signal', label: 'Signal' },
      { key: 'confidence', label: 'Confidence' },
      { key: 'entry_price', label: 'Entry Price' },
      { key: 'target', label: 'Target' },
      { key: 'stop_loss', label: 'Stop Loss' },
      { key: 'rr_ratio', label: 'R/R Ratio' },
      { key: 'strategy', label: 'Strategy' },
      { key: 'result', label: 'Result' },
    ]

    return this.exportCSV(signals, `jarvis_signals_${new Date().toISOString().split('T')[0]}.csv`, { columns })
  }

  /**
   * Generate PDF report (canvas-based, no library needed)
   */
  async exportPDF(reportData) {
    const { title = 'JARVIS Portfolio Report', sections = [], summary = {} } = reportData

    // Create a printable HTML document
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      // Fallback: download as HTML
      return this._exportAsHTML(reportData)
    }

    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>${title}</title>
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 40px; color: #1a1a1a; }
          .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #1f6feb; padding-bottom: 20px; }
          .header h1 { font-size: 24px; color: #0d1117; }
          .header .subtitle { color: #666; font-size: 14px; margin-top: 5px; }
          .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }
          .summary-card { background: #f6f8fa; border-radius: 8px; padding: 15px; text-align: center; }
          .summary-card .label { font-size: 11px; color: #666; text-transform: uppercase; }
          .summary-card .value { font-size: 20px; font-weight: 700; margin-top: 5px; }
          .green { color: #3fb950; }
          .red { color: #f85149; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 12px; }
          th { background: #0d1117; color: #fff; padding: 8px 10px; text-align: left; }
          td { padding: 6px 10px; border-bottom: 1px solid #e1e4e8; }
          tr:nth-child(even) td { background: #f9fafb; }
          .section-title { font-size: 16px; font-weight: 700; margin: 20px 0 10px; color: #0d1117; }
          .footer { text-align: center; color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #e1e4e8; padding-top: 15px; }
          @media print { body { padding: 20px; } .no-print { display: none; } }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>🤖 ${title}</h1>
          <div class="subtitle">Generated on ${new Date().toLocaleDateString('en-IN', { dateStyle: 'full' })} at ${new Date().toLocaleTimeString('en-IN')}</div>
        </div>

        ${summary ? `
          <div class="summary">
            ${Object.entries(summary).map(([k, v]) => `
              <div class="summary-card">
                <div class="label">${k.replace(/_/g, ' ')}</div>
                <div class="value ${typeof v === 'number' && v > 0 ? 'green' : typeof v === 'number' && v < 0 ? 'red' : ''}">
                  ${typeof v === 'number' ? (k.includes('pct') ? v.toFixed(2) + '%' : '₹' + v.toLocaleString()) : v}
                </div>
              </div>
            `).join('')}
          </div>
        ` : ''}

        ${sections.map(section => `
          <div class="section-title">${section.title}</div>
          ${section.data?.length ? `
            <table>
              <thead><tr>${Object.keys(section.data[0]).map(k => `<th>${k.replace(/_/g, ' ').toUpperCase()}</th>`).join('')}</tr></thead>
              <tbody>
                ${section.data.map(row => `<tr>${Object.values(row).map(v => `<td>${v ?? '-'}</td>`).join('')}</tr>`).join('')}
              </tbody>
            </table>
          ` : '<p>No data available</p>'}
        `).join('')}

        <div class="footer">
          JARVIS AI Trading Agent — Confidential Report<br>
          This report is auto-generated and should not be considered as financial advice.
        </div>

        <div class="no-print" style="text-align:center;margin-top:20px;">
          <button onclick="window.print()" style="padding:10px 30px;background:#1f6feb;color:white;border:none;border-radius:6px;cursor:pointer;font-size:14px;">
            📄 Print / Save as PDF
          </button>
        </div>
      </body>
      </html>
    `

    printWindow.document.write(html)
    printWindow.document.close()
    return true
  }

  _exportAsHTML(reportData) {
    const content = JSON.stringify(reportData, null, 2)
    this._download(content, 'jarvis_report.json', 'application/json')
    return true
  }

  /**
   * Generate P&L Summary report
   */
  generatePnLSummary(holdings = [], trades = []) {
    const totalInvestment = holdings.reduce((s, h) => s + ((h.avg_price || 0) * (h.quantity || 0)), 0)
    const currentValue = holdings.reduce((s, h) => s + ((h.current_price || 0) * (h.quantity || 0)), 0)
    const totalPnL = currentValue - totalInvestment
    const pnlPct = totalInvestment > 0 ? (totalPnL / totalInvestment) * 100 : 0

    const winners = holdings.filter(h => (h.pnl || 0) > 0).length
    const losers = holdings.filter(h => (h.pnl || 0) < 0).length

    return {
      title: 'JARVIS P&L Report',
      summary: {
        total_investment: totalInvestment,
        current_value: currentValue,
        total_pnl: totalPnL,
        pnl_pct: pnlPct,
        winners,
        losers,
        win_rate_pct: holdings.length > 0 ? (winners / holdings.length) * 100 : 0,
        total_trades: trades.length,
      },
      sections: [
        { title: '📈 Current Holdings', data: holdings },
        { title: '📋 Recent Trades', data: trades.slice(0, 50) },
      ]
    }
  }

  // Utility: trigger file download
  _download(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
}

const exportEngine = new PortfolioExportEngine()
export default exportEngine
