import { Search } from 'lucide-react'
import ExpenseTable from '../components/ExpenseTable'

export default function Transactions({ expenses, query, setQuery, onDelete, onEdit }) {
  const filtered = expenses.filter((item) => `${item.description} ${item.category}`.toLowerCase().includes(query.toLowerCase()))
  return <section className="view-section"><div className="section-heading"><div><span className="section-index">YOUR LEDGER</span><h2>All transactions <span className="count">{expenses.length}</span></h2></div><div className="search-box"><Search size={16} /><input placeholder="Search transactions" value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Search transactions" /></div></div>{filtered.length || !query ? <ExpenseTable expenses={filtered} onDelete={onDelete} onEdit={onEdit} /> : <div className="empty"><strong>No matching transactions</strong><span>Try a different search.</span></div>}</section>
}
