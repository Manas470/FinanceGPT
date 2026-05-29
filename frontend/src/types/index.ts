/** FinanceGPT shared TypeScript types */

export interface User {
  id: string
  email: string
  full_name: string
  role: 'super_admin' | 'cfo' | 'auditor' | 'analyst' | 'viewer'
  is_active: boolean
  company_id: string | null
  created_at: string
}

export interface Document {
  id: string
  filename: string
  original_filename: string
  file_size: number
  mime_type: string
  doc_type: DocumentType
  status: 'pending' | 'processing' | 'processed' | 'failed'
  period_start: string | null
  period_end: string | null
  created_at: string
  processed_at: string | null
}

export type DocumentType =
  | 'profit_loss'
  | 'balance_sheet'
  | 'cash_flow'
  | 'trial_balance'
  | 'general_ledger'
  | 'annual_report'
  | 'invoice'
  | 'other'

export interface AuditReport {
  id: string
  title: string
  period: string | null
  status: 'generating' | 'completed' | 'failed'
  risk_level: 'low' | 'medium' | 'high' | 'critical' | null
  overall_health_score: number | null
  liquidity_score: number | null
  profitability_score: number | null
  solvency_score: number | null
  efficiency_score: number | null
  executive_summary: string | null
  key_findings: Finding[] | null
  risk_matrix: RiskMatrix | null
  recommendations: Recommendation[] | null
  kpis: KPIs | null
  created_at: string
  completed_at: string | null
}

export interface Finding {
  category: string
  severity: Severity
  title: string
  detail: string
  impact: string
  recommendation: string
}

export interface RiskMatrix {
  financial_reporting: RiskLevel
  liquidity: RiskLevel
  operational: RiskLevel
  compliance: RiskLevel
  fraud: RiskLevel
  market: RiskLevel
}

export interface Recommendation {
  priority: 'immediate' | 'short_term' | 'long_term'
  category: string
  action: string
  owner: string
  expected_impact: string
}

export interface KPIs {
  revenue?: number | null
  gross_profit?: number | null
  gross_margin_pct?: number | null
  ebitda?: number | null
  net_income?: number | null
  net_margin_pct?: number | null
  current_ratio?: number | null
  quick_ratio?: number | null
  debt_to_equity?: number | null
  return_on_equity?: number | null
  return_on_assets?: number | null
  operating_cash_flow?: number | null
  free_cash_flow?: number | null
  [key: string]: number | null | undefined
}

export interface Anomaly {
  id: string
  anomaly_type: AnomalyType
  severity: Severity
  status: 'open' | 'under_review' | 'resolved' | 'false_positive'
  title: string
  description: string
  ai_explanation: string | null
  recommendation: string | null
  line_item: string | null
  amount: number | null
  expected_amount: number | null
  variance_pct: number | null
  confidence_score: number | null
  created_at: string
}

export type AnomalyType =
  | 'unusual_variance'
  | 'missing_data'
  | 'ratio_outlier'
  | 'trend_reversal'
  | 'duplicate_entry'
  | 'round_number'
  | 'year_end_spike'
  | 'intercompany'
  | 'unreconciled'
  | 'policy_breach'

export type Severity = 'info' | 'low' | 'medium' | 'high' | 'critical'
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

export interface DashboardMetrics {
  total_documents: number
  total_reports: number
  open_anomalies: number
  critical_anomalies: number
  avg_health_score: number | null
  recent_reports: AuditReport[]
  recent_anomalies: Anomaly[]
}

export interface Integration {
  id: string
  provider: 'quickbooks' | 'xero' | 'manual'
  status: 'active' | 'expired' | 'revoked' | 'error'
  is_active: boolean
  external_company_name: string | null
  last_synced_at: string | null
}
