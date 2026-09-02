export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  avatarInitials: string;
}

export interface InvestigationData {
  status: 'Not started' | 'In progress' | 'Root cause identified' | 'Remediated' | 'Closed';
  analystHypothesis: string;
  rootCause: string;
  recommendedRemediations: string[];
  executedRemediations: {
    action: string;
    executedBy: 'Human' | 'Agent';
    authorName: string;
    timestamp: string;
  }[];
  notes: {
    id: string;
    author: string;
    role: string;
    type: 'human' | 'agent';
    content: string;
    timestamp: string;
  }[];
}

export interface EvidenceItem {
  id: string;
  description: string;
  validationStatus: 'pending' | 'validated' | 'rejected';
  validatedBy: string;
  timestamp: string;
}

export interface AgentTimelineItem {
  id: string;
  step: string;
  skillCalled: string;
  status: 'success' | 'failed' | 'running';
  timestamp: string;
  details: string;
  feedback?: {
    verdict: 'correct' | 'incorrect';
    comment?: string;
  };
}

export interface Alert {
  id: string;
  title: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  source: string;
  client: string;
  status: 'New' | 'Analyzed' | 'Escalated' | 'False Positive';
  timestamp: string;
  rawPayload: string;
}

export interface Ticket {
  id: string;
  title: string;
  client: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  status: 'New' | 'Assigned' | 'In Progress' | 'Pending' | 'Escalated' | 'Resolved';
  assignedTo: string;
  openedDaysAgo: number;
  slaBreach: boolean;
  evidence: EvidenceItem[];
  timeline: AgentTimelineItem[];
  investigation: InvestigationData;
}

export interface Correlation {
  id: string;
  title: string;
  entities: string[];
  confidence: number;
  timestamp: string;
  summary: string;
  riskScore: number;
}

export interface IOC {
  id: string;
  type: 'IP' | 'Domain' | 'Hash' | 'URL';
  value: string;
  source: string;
  confidence: number;
  firstSeen: string;
  lastSeen: string;
  threatActor?: string;
}

export interface PlaybookTemplate {
  id: string;
  name: string;
  category: string;
  triggers: string;
  skillsSequence: string[];
  autoExecute: boolean;
  version: string;
}

export interface ReviewItem {
  id: string;
  title: string;
  agentDecision: string;
  recommendedAction: string;
  client: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  timestamp: string;
  confidence: number;
  evidenceSummary: string;
}

export interface AIGymScenario {
  id: string;
  name: string;
  skillType: 'Splunk' | 'Elastic' | 'ThreatIntel' | 'EDR';
  query: string;
  selectedSkill: string;
  routerConfidence: number;
  executionTimeMs: number;
  resultStatus: 'Success' | 'Warning' | 'Error';
  feedbackVerdict?: 'correct' | 'incorrect';
}

export interface AIPerformanceMetrics {
  overallAccuracy: number;
  falsePositiveRate: number;
  avgHandlingTimeSec: number;
  skillLatencies: { skill: string; latencyMs: number; usageCount: number }[];
  accuracyByType: { category: string; accuracy: number }[];
  feedbackSummary: {
    positiveCount: number;
    negativeCount: number;
    skillAccuracies: { skill: string; accuracy: number }[];
    recentComments: { id: string; itemTitle: string; comment: string; verdict: 'correct' | 'incorrect'; author: string; timestamp: string }[];
  };
}

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: string;
  mcpConnectors: { name: string; status: 'Connected' | 'Degraded' | 'Offline'; latency: string }[];
}

export interface ClientTenant {
  id: string;
  name: string;
  industry: string;
  activeAlerts: number;
  openTickets: number;
  riskScore: 'Low' | 'Medium' | 'High' | 'Critical';
  mcpProvider: 'Splunk' | 'Elastic' | 'Mixed';
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: 'alert' | 'ticket' | 'review' | 'system';
  timestamp: string;
  read: boolean;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  skillUsed?: string;
  skillCallMeta?: {
    skill: string;
    query?: string;
    status: 'running' | 'success' | 'failed';
    summary?: string;
  };
}
