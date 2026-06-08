import { MetricCard } from '@/components/Common/Common'
import { Summary } from '@/types'
import { BarChart3, CheckCircle, TrendingUp } from 'lucide-react'

interface SummaryMetricsProps {
  summary: Summary
}

export default function SummaryMetrics({ summary }: SummaryMetricsProps) {
  const metrics = [
    {
      label: 'Total Audits',
      value: summary.total_audits,
      icon: <BarChart3 className="w-6 h-6" />,
    },
    {
      label: 'Completion Rate',
      value: summary.completion_rate?.toFixed(1) || 0,
      unit: '%',
      icon: <CheckCircle className="w-6 h-6" />,
    },
    {
      label: 'Avg Final Score',
      value: summary.average_final_score?.toFixed(1) || 0,
      unit: '%',
      icon: <TrendingUp className="w-6 h-6" />,
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {metrics.map((metric, index) => (
        <MetricCard
          key={index}
          label={metric.label}
          value={metric.value}
          unit={metric.unit}
          icon={metric.icon}
        />
      ))}
    </div>
  )
}
