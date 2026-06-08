import { useAnalytics } from '@/hooks/useApi'
import { Loading, Error, Card } from '@/components/Common/Common'
import SummaryMetrics from './SummaryMetrics'
import TrendChart from './Charts/TrendChart'

export default function DashboardContent() {
  const { data, loading, error, execute } = useAnalytics()

  if (loading) {
    return <Loading />
  }

  if (error) {
    return (
      <Error
        message="Failed to load analytics data"
        onRetry={execute}
      />
    )
  }

  if (!data) {
    return (
      <Card className="p-8 text-center">
        <p className="text-gray-600 font-medium">No data available</p>
        <p className="text-gray-500 text-sm mt-2">Upload a QA data file to get started</p>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <SummaryMetrics summary={data.summary} />
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Score Trend</h3>
        <TrendChart audits={data.audits} />
      </Card>
    </div>
  )
}
