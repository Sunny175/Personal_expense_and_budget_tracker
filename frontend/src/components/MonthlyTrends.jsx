import { useEffect, useState } from 'react'
import { request } from '../api/client'
import { money, monthLabel, trendMonths } from '../utils/format'

export default function MonthlyTrends({ month, revision }) {
  const [state, setState] = useState({ loading: true, data: [], error: '' })
  useEffect(() => {
    let active = true
    setState({ loading: true, data: [], error: '' })
    const months = trendMonths(month)
    Promise.all(months.map((value) => request(`/api/summary?month=${value}`)))
      .then((data) => { if (active) setState({ loading: false, data, error: '' }) })
      .catch((error) => { if (active) setState({ loading: false, data: [], error: error.message }) })
    return () => { active = false }
  }, [month, revision])
  const max = Math.max(0, ...state.data.map((item) => Number(item.total_spent)))
  return <section className="trend-section">
    <div className="section-heading"><div><span className="section-index">04 / OVER TIME</span><h2>Monthly spending</h2><p className="section-subtitle">Six months ending {monthLabel(month)}</p></div></div>
    {state.loading ? <div className="trend-message">Loading trends...</div> : state.error ? <div className="trend-message form-error" role="alert">Could not load trends: {state.error}</div> : <div className="trend-list">
      {state.data.map((item) => <div className="trend-row" key={item.month}><span>{monthLabel(item.month)}</span><div className="trend-track" aria-hidden="true"><span style={{ width: `${max ? Number(item.total_spent) / max * 100 : 0}%` }} /></div><strong>{money(item.total_spent)}</strong></div>)}
    </div>}
  </section>
}
