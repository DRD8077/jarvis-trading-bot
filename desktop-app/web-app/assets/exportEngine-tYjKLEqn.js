class c{exportCSV(e,o="jarvis_export.csv",l={}){if(!(e!=null&&e.length))return console.warn("[Export] No data to export"),!1;const s=l.columns||Object.keys(e[0]).map(a=>({key:a,label:a}));let r=s.map(a=>`"${a.label}"`).join(",")+`
`;for(const a of e){const i=s.map(n=>{let t=a[n.key];return t==null&&(t=""),typeof t=="object"&&(t=JSON.stringify(t)),t=String(t).replace(/"/g,'""'),`"${t}"`});r+=i.join(",")+`
`}return this._download(r,o,"text/csv;charset=utf-8;"),!0}exportPortfolio(e){if(!(e!=null&&e.length))return!1;const o=[{key:"symbol",label:"Symbol"},{key:"name",label:"Name"},{key:"quantity",label:"Quantity"},{key:"avg_price",label:"Avg Price"},{key:"current_price",label:"Current Price"},{key:"pnl",label:"P&L"},{key:"pnl_pct",label:"P&L %"},{key:"value",label:"Total Value"},{key:"exchange",label:"Exchange"}],l=new Date().toISOString().split("T")[0];return this.exportCSV(e,`jarvis_portfolio_${l}.csv`,{columns:o})}exportTradeJournal(e){if(!(e!=null&&e.length))return!1;const o=[{key:"date",label:"Date"},{key:"time",label:"Time"},{key:"symbol",label:"Symbol"},{key:"side",label:"Side"},{key:"type",label:"Type"},{key:"quantity",label:"Quantity"},{key:"price",label:"Price"},{key:"total",label:"Total"},{key:"fee",label:"Fee"},{key:"pnl",label:"Realized P&L"},{key:"exchange",label:"Exchange"},{key:"strategy",label:"Strategy"},{key:"notes",label:"Notes"}],l=new Date().toISOString().split("T")[0];return this.exportCSV(e,`jarvis_trades_${l}.csv`,{columns:o})}exportSignals(e){if(!(e!=null&&e.length))return!1;const o=[{key:"timestamp",label:"Time"},{key:"symbol",label:"Symbol"},{key:"signal",label:"Signal"},{key:"confidence",label:"Confidence"},{key:"entry_price",label:"Entry Price"},{key:"target",label:"Target"},{key:"stop_loss",label:"Stop Loss"},{key:"rr_ratio",label:"R/R Ratio"},{key:"strategy",label:"Strategy"},{key:"result",label:"Result"}];return this.exportCSV(e,`jarvis_signals_${new Date().toISOString().split("T")[0]}.csv`,{columns:o})}async exportPDF(e){const{title:o="JARVIS Portfolio Report",sections:l=[],summary:s={}}=e,r=window.open("","_blank");if(!r)return this._exportAsHTML(e);const a=`
      <!DOCTYPE html>
      <html>
      <head>
        <title>${o}</title>
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
          <h1>🤖 ${o}</h1>
          <div class="subtitle">Generated on ${new Date().toLocaleDateString("en-IN",{dateStyle:"full"})} at ${new Date().toLocaleTimeString("en-IN")}</div>
        </div>

        ${s?`
          <div class="summary">
            ${Object.entries(s).map(([i,n])=>`
              <div class="summary-card">
                <div class="label">${i.replace(/_/g," ")}</div>
                <div class="value ${typeof n=="number"&&n>0?"green":typeof n=="number"&&n<0?"red":""}">
                  ${typeof n=="number"?i.includes("pct")?n.toFixed(2)+"%":"₹"+n.toLocaleString():n}
                </div>
              </div>
            `).join("")}
          </div>
        `:""}

        ${l.map(i=>{var n;return`
          <div class="section-title">${i.title}</div>
          ${(n=i.data)!=null&&n.length?`
            <table>
              <thead><tr>${Object.keys(i.data[0]).map(t=>`<th>${t.replace(/_/g," ").toUpperCase()}</th>`).join("")}</tr></thead>
              <tbody>
                ${i.data.map(t=>`<tr>${Object.values(t).map(p=>`<td>${p??"-"}</td>`).join("")}</tr>`).join("")}
              </tbody>
            </table>
          `:"<p>No data available</p>"}
        `}).join("")}

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
    `;return r.document.write(a),r.document.close(),!0}_exportAsHTML(e){const o=JSON.stringify(e,null,2);return this._download(o,"jarvis_report.json","application/json"),!0}generatePnLSummary(e=[],o=[]){const l=e.reduce((t,p)=>t+(p.avg_price||0)*(p.quantity||0),0),s=e.reduce((t,p)=>t+(p.current_price||0)*(p.quantity||0),0),r=s-l,a=l>0?r/l*100:0,i=e.filter(t=>(t.pnl||0)>0).length,n=e.filter(t=>(t.pnl||0)<0).length;return{title:"JARVIS P&L Report",summary:{total_investment:l,current_value:s,total_pnl:r,pnl_pct:a,winners:i,losers:n,win_rate_pct:e.length>0?i/e.length*100:0,total_trades:o.length},sections:[{title:"📈 Current Holdings",data:e},{title:"📋 Recent Trades",data:o.slice(0,50)}]}}_download(e,o,l){const s=new Blob([e],{type:l}),r=URL.createObjectURL(s),a=document.createElement("a");a.href=r,a.download=o,document.body.appendChild(a),a.click(),document.body.removeChild(a),URL.revokeObjectURL(r)}}const b=new c;export{b as default};
