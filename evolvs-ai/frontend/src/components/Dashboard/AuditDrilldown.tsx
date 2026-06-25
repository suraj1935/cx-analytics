import { useState, useMemo } from 'react'
import { useAuditDetails } from '@/hooks/useApi'
import { Card, Loading, Error } from '@/components/Common/Common'
import { 
  Search, Eye, X, AlertOctagon, CheckCircle2, 
  Clock, ShieldAlert, FileSpreadsheet
} from 'lucide-react'
import { Audit } from '@/types'

interface AuditDrilldownProps {
  audits: Audit[]
}

export default function AuditDrilldown({ audits }: AuditDrilldownProps) {
  const [search, setSearch] = useState('')
  const [selectedProject, setSelectedProject] = useState('All')
  const [selectedPriority, setSelectedPriority] = useState('All')
  const [selectedStatus, setSelectedStatus] = useState('All')
  const [selectedSla, setSelectedSla] = useState('All')
  const [selectedAuditId, setSelectedAuditId] = useState<string | null>(null)

  // Unique filter lists
  const projects = useMemo(() => ['All', ...Array.from(new Set(audits.map(a => a.project).filter(Boolean)))], [audits])
  const priorities = useMemo(() => ['All', ...Array.from(new Set(audits.map(a => a.priority).filter(Boolean)))], [audits])
  const statuses = useMemo(() => ['All', ...Array.from(new Set(audits.map(a => a.status).filter(Boolean)))], [audits])

  // Filtered audits
  const filteredAudits = useMemo(() => {
    return audits.filter(audit => {
      const matchesSearch = 
        (audit.audit_id && audit.audit_id.toLowerCase().includes(search.toLowerCase())) ||
        (audit.qa && audit.qa.toLowerCase().includes(search.toLowerCase())) ||
        (audit.manager && audit.manager.toLowerCase().includes(search.toLowerCase())) ||
        (audit.source_external_id && String(audit.source_external_id).toLowerCase().includes(search.toLowerCase()))
      
      const matchesProject = selectedProject === 'All' || audit.project === selectedProject
      const matchesPriority = selectedPriority === 'All' || audit.priority === selectedPriority
      const matchesStatus = selectedStatus === 'All' || audit.status === selectedStatus
      
      let matchesSla = true
      if (selectedSla !== 'All') {
        const breached = audit.sla_breached === 1 || audit.sla_breached === 'Yes' || audit.sla_breached === true
        matchesSla = selectedSla === 'Breached' ? breached : !breached
      }

      return matchesSearch && matchesProject && matchesPriority && matchesStatus && matchesSla
    })
  }, [audits, search, selectedProject, selectedPriority, selectedStatus, selectedSla])

  return (
    <div className="space-y-6 relative">
      {/* Filters Bar */}
      <Card className="p-4 bg-white shadow-sm border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="relative col-span-1 md:col-span-2">
            <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by ID, Agent, Manager, External ID..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          <div>
            <select
              value={selectedProject}
              onChange={e => setSelectedProject(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            >
              <option value="All">All Projects</option>
              {projects.map(p => p !== 'All' && <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div>
            <select
              value={selectedPriority}
              onChange={e => setSelectedPriority(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            >
              <option value="All">All Priorities</option>
              {priorities.map(p => p !== 'All' && <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div>
            <select
              value={selectedStatus}
              onChange={e => setSelectedStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            >
              <option value="All">All Statuses</option>
              {statuses.map(s => s !== 'All' && <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <div>
            <select
              value={selectedSla}
              onChange={e => setSelectedSla(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            >
              <option value="All">All SLA Status</option>
              <option value="On Track">On Track</option>
              <option value="Breached">Breached</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Audits Table */}
      <Card className="overflow-hidden border border-gray-200">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left py-3.5 px-4 font-semibold text-gray-700">Audit ID</th>
                <th className="text-left py-3.5 px-4 font-semibold text-gray-700">Project</th>
                <th className="text-left py-3.5 px-4 font-semibold text-gray-700">QA / Manager</th>
                <th className="text-center py-3.5 px-4 font-semibold text-gray-700">Final Score</th>
                <th className="text-center py-3.5 px-4 font-semibold text-gray-700">System Score</th>
                <th className="text-center py-3.5 px-4 font-semibold text-gray-700">Priority</th>
                <th className="text-center py-3.5 px-4 font-semibold text-gray-700">SLA</th>
                <th className="text-center py-3.5 px-4 font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {filteredAudits.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-gray-500 font-medium">
                    No audits found matching the selected filters.
                  </td>
                </tr>
              ) : (
                filteredAudits.map((audit) => {
                  const score = audit.final_score || 0
                  const scoreColor = score >= 85 ? 'text-green-600 font-bold' : score >= 75 ? 'text-yellow-600 font-semibold' : 'text-red-600 font-bold'
                  const priorityColor = 
                    audit.priority === 'High' ? 'bg-red-50 text-red-700 border-red-100' :
                    audit.priority === 'Medium' ? 'bg-amber-50 text-amber-700 border-amber-100' :
                    'bg-blue-50 text-blue-700 border-blue-100'
                  
                  const isSlaBreached = audit.sla_breached === 1 || audit.sla_breached === 'Yes' || audit.sla_breached === true

                  return (
                    <tr key={audit.audit_id} className="hover:bg-gray-50 transition-colors">
                      <td className="py-4 px-4 font-medium text-gray-900">
                        <div className="truncate max-w-[150px] font-mono text-xs" title={audit.audit_id}>
                          {audit.audit_id}
                        </div>
                        {audit.source_external_id && (
                          <div className="text-xs text-gray-500 mt-0.5">Ext: {audit.source_external_id}</div>
                        )}
                      </td>
                      <td className="py-4 px-4 text-gray-600 font-medium">{audit.project}</td>
                      <td className="py-4 px-4">
                        <div className="font-medium text-gray-900">{audit.qa}</div>
                        <div className="text-xs text-gray-500">Mgr: {audit.manager}</div>
                      </td>
                      <td className="py-4 px-4 text-center">
                        <span className={`text-base ${scoreColor}`}>{score.toFixed(1)}%</span>
                      </td>
                      <td className="py-4 px-4 text-center text-gray-600">
                        {(audit.system_score || 0).toFixed(1)}%
                      </td>
                      <td className="py-4 px-4 text-center">
                        <span className={`inline-block px-2.5 py-0.5 rounded-full border text-xs font-semibold ${priorityColor}`}>
                          {audit.priority}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-center">
                        {isSlaBreached ? (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-600 bg-red-50 px-2 py-1 rounded-full">
                            <Clock className="w-3.5 h-3.5" />
                            Breached
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-green-600 bg-green-50 px-2 py-1 rounded-full">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            On Track
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-4 text-center">
                        <button
                          onClick={() => setSelectedAuditId(audit.audit_id)}
                          className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors inline-flex items-center gap-1"
                        >
                          <Eye className="w-4 h-4" />
                          <span className="text-xs font-semibold">View Detail</span>
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Slide-out detail drawer */}
      {selectedAuditId && (
        <AuditDetailDrawer 
          auditId={selectedAuditId} 
          onClose={() => setSelectedAuditId(null)} 
          audit={audits.find(a => a.audit_id === selectedAuditId)!}
        />
      )}
    </div>
  )
}

interface DetailDrawerProps {
  auditId: string
  onClose: () => void
  audit: Audit
}

function AuditDetailDrawer({ auditId, onClose, audit }: DetailDrawerProps) {
  const { data: parameters, loading, error } = useAuditDetails(auditId)

  // Group parameters by category
  const groupedParameters = useMemo(() => {
    if (!parameters) return {}
    return parameters.reduce((acc, curr) => {
      const cat = curr.category || 'General'
      if (!acc[cat]) acc[cat] = []
      acc[cat].push(curr)
      return acc
    }, {} as Record<string, any[]>)
  }, [parameters])

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 w-full md:max-w-2xl bg-white shadow-2xl z-50 flex flex-col border-l border-gray-100 transform transition-transform duration-300 ease-out font-sans">
        {/* Header */}
        <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-slate-900 to-indigo-950 text-white">
          <div>
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-bold">Audit Detail Analysis</h2>
            </div>
            <p className="text-xs text-slate-300 mt-1 font-mono">ID: {auditId}</p>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-300 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Metadata Card */}
          <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
            <div>
              <p className="text-xs text-gray-500 font-medium">Project</p>
              <p className="text-sm font-semibold text-gray-900 mt-0.5">{audit.project}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Status</p>
              <p className="text-sm font-semibold text-gray-900 mt-0.5">{audit.status}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">QA Inspector</p>
              <p className="text-sm font-semibold text-gray-900 mt-0.5">{audit.qa}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Manager</p>
              <p className="text-sm font-semibold text-gray-900 mt-0.5">{audit.manager}</p>
            </div>
          </div>

          {/* Scores Overview Card */}
          <div className="grid grid-cols-2 gap-4 bg-gradient-to-br from-blue-50 to-indigo-50/50 p-4 rounded-xl border border-blue-100/50">
            <div className="text-center py-2">
              <p className="text-xs text-indigo-700 font-semibold uppercase tracking-wider">Final QA Score</p>
              <p className="text-3xl font-extrabold text-blue-900 mt-1">{(audit.final_score || 0).toFixed(1)}%</p>
            </div>
            <div className="text-center py-2 border-l border-indigo-100">
              <p className="text-xs text-indigo-700 font-semibold uppercase tracking-wider">AI System Score</p>
              <p className="text-3xl font-extrabold text-indigo-900 mt-1">{(audit.system_score || 0).toFixed(1)}%</p>
            </div>
          </div>

          {/* Audit Parameters Details */}
          <div>
            <h3 className="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wider">Parameters Checklist</h3>
            
            {loading && <Loading />}
            {error && <Error message="Could not load parameter details." />}
            
            {parameters && (
              <div className="space-y-6">
                {Object.entries(groupedParameters).map(([category, items]) => (
                  <div key={category} className="space-y-3">
                    <h4 className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-md inline-block">
                      {category}
                    </h4>

                    <div className="space-y-3">
                      {(items as any[]).map((item: any, idx: number) => {
                        const thresholdPassed = item.threshold_passed === 'Yes' || item.threshold_passed === true || item.threshold_passed === 1
                        const hasAutoFail = item.auto_fail === 'Yes' || item.auto_fail === true || item.auto_fail === 1
                        const hasFailureReason = item.reason && String(item.reason).trim() !== ''

                        return (
                          <div 
                            key={idx} 
                            className={`p-4 rounded-xl border transition-all ${
                              hasAutoFail 
                                ? 'bg-red-50/40 border-red-200' 
                                : !thresholdPassed 
                                  ? 'bg-amber-50/30 border-amber-200' 
                                  : 'bg-white border-gray-150 hover:shadow-sm'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div>
                                <div className="flex items-center gap-2">
                                  <h5 className="font-semibold text-gray-900 text-sm">{item.label}</h5>
                                  {item.weight && (
                                    <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-bold">
                                      W: {item.weight}
                                    </span>
                                  )}
                                </div>
                                {item.guideline && (
                                  <p className="text-xs text-slate-500 mt-0.5 font-medium">{item.guideline}</p>
                                )}
                              </div>

                              <div className="flex items-center gap-3 shrink-0">
                                <div className="text-right">
                                  <div className="text-xs text-gray-500 font-medium">QA Score</div>
                                  <div className={`font-bold text-sm ${thresholdPassed ? 'text-green-600' : 'text-amber-600'}`}>
                                    {(item.qa_score || 0).toFixed(0)}
                                  </div>
                                </div>
                                <div className="text-right border-l border-gray-200 pl-3">
                                  <div className="text-xs text-gray-500 font-medium">AI Score</div>
                                  <div className="font-semibold text-gray-700 text-sm">
                                    {(item.system_score || 0).toFixed(0)}
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Failure details if any */}
                            {(hasAutoFail || !thresholdPassed || hasFailureReason) && (
                              <div className="mt-3 bg-white p-3 rounded-lg border border-slate-100 space-y-2">
                                {hasAutoFail && (
                                  <div className="flex items-center gap-2 text-red-600 text-xs font-bold">
                                    <ShieldAlert className="w-4 h-4 shrink-0" />
                                    <span>Auto Fail Triggered</span>
                                  </div>
                                )}
                                {!thresholdPassed && (
                                  <div className="flex items-center gap-2 text-amber-600 text-xs font-semibold">
                                    <AlertOctagon className="w-4 h-4 shrink-0" />
                                    <span>Failed compliance score threshold</span>
                                  </div>
                                )}
                                {hasFailureReason && (
                                  <div className="text-xs text-slate-700">
                                    <span className="font-bold text-slate-900">Failure Reason:</span> {item.reason}
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Response content */}
                            {item.response && (
                              <div className="mt-3 text-xs text-slate-600 border-t border-slate-100/60 pt-2.5">
                                <span className="font-bold text-slate-700 block mb-1">Audit Response Snippet:</span>
                                <p className="bg-slate-50 p-2.5 rounded-lg border border-slate-100 font-mono text-[11px] leading-relaxed">
                                  {item.response}
                                </p>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
