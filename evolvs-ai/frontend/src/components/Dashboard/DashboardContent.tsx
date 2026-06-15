import { useState } from 'react'
import { useAnalytics } from '@/hooks/useApi'
import { Loading, Error, Card } from '@/components/Common/Common'
import SummaryMetrics from './SummaryMetrics'
import TrendChart from './Charts/TrendChart'
import AuditDrilldown from './AuditDrilldown'
import { Agent, Parameter } from '@/types'
import { Users, AlertTriangle, CheckCircle, XCircle, BarChart2, Table } from 'lucide-react'

function AgentTable({ agents }: { agents: Agent[] }) {
  if (agents.length === 0) return null

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Users className="w-5 h-5 text-blue-600" />
        Agent Performance
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 font-semibold text-gray-700">Agent</th>
              <th className="text-center py-3 px-4 font-semibold text-gray-700">Audits</th>
              <th className="text-center py-3 px-4 font-semibold text-gray-700">Avg Score</th>
              <th className="text-center py-3 px-4 font-semibold text-gray-700">Completion</th>
              <th className="text-center py-3 px-4 font-semibold text-gray-700">SLA</th>
              <th className="text-center py-3 px-4 font-semibold text-gray-700">Disputes</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((agent, i) => {
              const score = agent.average_final_score || 0
              const scoreColor = score >= 85 ? 'text-green-600' : score >= 70 ? 'text-yellow-600' : 'text-red-600'
              const completion = ((agent.completion_rate || 0) * 100)
              const sla = agent.sla_adherence || 0
              
              return (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="py-3 px-4 font-medium text-gray-900">{agent.agent}</td>
                  <td className="py-3 px-4 text-center text-gray-600">{agent.audits}</td>
                  <td className={`py-3 px-4 text-center font-semibold ${scoreColor}`}>
                    {score.toFixed(1)}%
                  </td>
                  <td className="py-3 px-4 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full transition-all" 
                          style={{ width: `${Math.min(completion, 100)}%` }}
                        />
                      </div>
                      <span className="text-gray-600 text-xs">{completion.toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center text-gray-600">{sla.toFixed(1)}%</td>
                  <td className="py-3 px-4 text-center text-gray-600">
                    {((agent.dispute_rate || 0) * 100).toFixed(1)}%
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

function ParameterTable({ parameters }: { parameters: Parameter[] }) {
  if (parameters.length === 0) return null

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-amber-500" />
        Parameter Analytics
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 font-semibold text-gray-700">Parameter</th>
              <th className="text-center py-3 px-4 font-semibold text-gray-700">Category</th>
              <th className="text-center py-3 px-4 font-semibold text-gray-700">Pass Rate</th>
              <th className="text-center py-3 px-4 font-semibold text-gray-700">Failures</th>
              <th className="text-center py-3 px-4 font-semibold text-gray-700">Avg Score</th>
            </tr>
          </thead>
          <tbody>
            {parameters.map((param, i) => {
              const passRate = (param.pass_rate || 0) * 100
              const passColor = passRate >= 80 ? 'bg-green-100 text-green-700' : passRate >= 60 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
              
              return (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-medium text-gray-900">{param.label}</div>
                    <div className="text-xs text-gray-500">{param.criterion_key}</div>
                  </td>
                  <td className="py-3 px-4 text-center text-gray-600">{param.category || '—'}</td>
                  <td className="py-3 px-4 text-center">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${passColor}`}>
                      {passRate >= 80 ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                      {passRate.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center font-medium text-red-600">{param.failures}</td>
                  <td className="py-3 px-4 text-center text-gray-600">
                    {(param.average_score || 0).toFixed(1)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

type TabType = 'overview' | 'drilldown'

export default function DashboardContent() {
  const { data, loading, error, execute } = useAnalytics()
  const [activeTab, setActiveTab] = useState<TabType>('overview')

  if (loading) {
    return <Loading />
  }

  if (error) {
    return (
      <Error
        message="Failed to load analytics data. Make sure the backend is running."
        onRetry={execute}
      />
    )
  }

  if (!data || (data.summary.total_audits === 0 && data.audits.length === 0)) {
    return (
      <Card className="p-8 text-center">
        <p className="text-gray-600 font-medium">No data available</p>
        <p className="text-gray-500 text-sm mt-2">Upload a QA data file to get started</p>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Premium Tab Bar Navigation */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 py-3.5 px-6 font-semibold text-sm border-b-2 transition-all ${
            activeTab === 'overview'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          Analytics Overview
        </button>
        <button
          onClick={() => setActiveTab('drilldown')}
          className={`flex items-center gap-2 py-3.5 px-6 font-semibold text-sm border-b-2 transition-all ${
            activeTab === 'drilldown'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <Table className="w-4 h-4" />
          Detailed Dataset Drilldown
        </button>
      </div>

      {activeTab === 'overview' ? (
        <div className="space-y-6">
          <SummaryMetrics summary={data.summary} />
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Score Trend</h3>
            <TrendChart audits={data.audits} />
          </Card>
          <AgentTable agents={data.agents} />
          <ParameterTable parameters={data.parameters} />
        </div>
      ) : (
        <AuditDrilldown audits={data.audits} />
      )}
    </div>
  )
}
