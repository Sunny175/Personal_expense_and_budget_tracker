export const colors = ['#d57f69', '#789b91', '#d2ad63', '#8198ba', '#ab93b2', '#8ca8a3']
export const today = () => { const date = new Date(); return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}` }
export const money = (value) => Number(value || 0).toLocaleString('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2, maximumFractionDigits: 2 })
export const title = (text) => text.replace(/\b\w/g, (letter) => letter.toUpperCase())
export const monthLabel = (month) => new Date(Number(month.slice(0, 4)), Number(month.slice(5, 7)) - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
export const shiftMonth = (month, offset) => { const date = new Date(Number(month.slice(0, 4)), Number(month.slice(5, 7)) - 1 + offset, 1); return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}` }
export const trendMonths = (month) => Array.from({ length: 6 }, (_, index) => shiftMonth(month, index - 5))
export const shortDate = (date) => new Date(`${date}T12:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
