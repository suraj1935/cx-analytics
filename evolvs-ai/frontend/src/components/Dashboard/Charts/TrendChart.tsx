import { Audit } from '@/types'
import { 
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend 
} from 'recharts'

interface TrendChartProps {
  audits: Audit[]
}

interface ChartDataPoint {
  date: string
  'Average Score': number
  'System Score': number
}

export default function TrendChart({ audits }: TrendChartProps) {
  if (audits.length === 0) {
    return (
      <div className="h-72 flex flex-col items-center justify-center text-gray-500 bg-gray-50 rounded-xl border border-dashed border-gray-200">
        <p className="font-medium">No data available for trend chart</p>
      </div>
    )
  }

  // Group by date and calculate average scores
  const dataMap: { [date: string]: { finalSum: number; systemSum: number; count: number } } = {}

  audits.forEach((audit) => {
    try {
      const dateObj = new Date(audit.created_at)
      if (isNaN(dateObj.getTime())) return
      
      const dateStr = dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
      if (!dataMap[dateStr]) {
        dataMap[dateStr] = { finalSum: 0, systemSum: 0, count: 0 }
      }
      dataMap[dateStr].finalSum += audit.final_score
      dataMap[dateStr].systemSum += audit.system_score || 0
      dataMap[dateStr].count += 1
    } catch (e) {
      // Ignore invalid date formats
    }
  })

  // Convert map to sorted array
  const chartData: ChartDataPoint[] = Object.keys(dataMap)
    .map((date) => ({
      date,
      'Average Score': Math.round((dataMap[date].finalSum / dataMap[date].count) * 10) / 10,
      'System Score': Math.round((dataMap[date].systemSum / dataMap[date].count) * 10) / 10,
    }))
    // Optional: Sort dates if they have timestamps or can be parsed, or keep order of appearance.
    // For simplicity and correctness we sort them chronologically by parsing their dates.
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())

  return (
    <div className="h-72 w-full mt-2">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorFinal" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorSystem" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
          <XAxis 
            dataKey="date" 
            tickLine={false} 
            axisLine={false}
            tick={{ fill: '#9ca3af', fontSize: 12 }}
          />
          <YAxis 
            domain={[0, 100]} 
            tickLine={false} 
            axisLine={false}
            tick={{ fill: '#9ca3af', fontSize: 12 }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'rgba(255, 255, 255, 0.95)', 
              borderRadius: '12px', 
              border: '1px solid #e5e7eb',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)' 
            }}
          />
          <Legend 
            verticalAlign="top" 
            height={36} 
            iconType="circle"
          />
          <Area 
            type="monotone" 
            dataKey="Average Score" 
            stroke="#0ea5e9" 
            strokeWidth={3}
            fillOpacity={1} 
            fill="url(#colorFinal)" 
          />
          <Area 
            type="monotone" 
            dataKey="System Score" 
            stroke="#6366f1" 
            strokeWidth={2}
            strokeDasharray="4 4"
            fillOpacity={1} 
            fill="url(#colorSystem)" 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
