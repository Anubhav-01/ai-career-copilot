/** Typed mirrors of the FastAPI response schemas. */

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_admin: boolean;
  created_at: string;
}

export interface Profile {
  id: string;
  user_id: string;
  headline: string | null;
  location: string | null;
  phone: string | null;
  experience_years: number | null;
  education_level: string | null;
  target_roles: string[] | null;
  links: Record<string, string> | null;
}

export type ResumeStatus = "pending" | "processing" | "completed" | "failed";

export interface Resume {
  id: string;
  title: string;
  original_filename: string;
  file_type: string;
  status: ResumeStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExperienceItem {
  title: string;
  company: string;
  location: string | null;
  start_date: string | null;
  end_date: string | null;
  bullets: string[];
}

export interface EducationItem {
  degree: string;
  institution: string;
  field: string | null;
  start_year: string | null;
  end_year: string | null;
}

export interface ProjectItem {
  name: string;
  description: string;
  technologies: string[];
  url: string | null;
}

export interface ResumeExtraction {
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  summary: string | null;
  skills: string[];
  experience: ExperienceItem[];
  education: EducationItem[];
  projects: ProjectItem[];
  certifications: string[];
  achievements: string[];
  links: string[];
}

export interface ResumeSkill {
  name: string;
  normalized: string;
  category: string | null;
  evidence: string | null;
  source: string;
}

export interface ResumeSection {
  id: string;
  section_type: string;
  title: string | null;
  content: string;
  order_index: number;
}

export interface ResumeDetail extends Resume {
  parsed: ResumeExtraction | null;
  skills: ResumeSkill[];
  sections: ResumeSection[];
}

export interface ScoreComponent {
  key: string;
  label: string;
  score: number;
  weight: number;
  explanation: string;
}

export interface ATSFinding {
  severity: "info" | "warning" | "critical";
  category: string;
  problem: string;
  recommendation: string;
}

export interface ATSResult {
  score: number;
  findings: ATSFinding[];
  action_verb_count: number;
  quantified_bullet_ratio: number;
  detected_sections: string[];
  missing_sections: string[];
  keyword_stuffing_detected: boolean;
}

export interface Recommendation {
  priority: "high" | "medium" | "low";
  category: string;
  problem: string;
  recommendation: string;
}

export interface ResumeAnalysis {
  id: string;
  resume_id: string;
  overall_score: number;
  scores: { components: ScoreComponent[] };
  ats: ATSResult;
  recommendations: Recommendation[];
  explanation: string | null;
  weights: Record<string, number>;
  created_at: string;
}

export interface BulletImprovement {
  original: string;
  improved: string;
  rationale: string;
  missing_metric_suggestion: string | null;
}

export interface TailoringSuggestion {
  skills_to_emphasize: string[];
  keywords_to_include: string[];
  sections_to_modify: string[];
  bullets_to_improve: string[];
  missing_evidence: string[];
  summary: string;
}

export interface JobAnalysis {
  job_title: string;
  company: string;
  required_skills: string[];
  preferred_skills: string[];
  education: string[];
  experience_years_min: number | null;
  responsibilities: string[];
  tools: string[];
  technologies: string[];
  keywords: string[];
  seniority: string | null;
}

export interface Job {
  id: string;
  title: string;
  company: string | null;
  location: string | null;
  source_url: string | null;
  created_at: string;
}

export interface JobDetail extends Job {
  description_text: string;
  analysis: JobAnalysis | null;
}

export interface MatchComponents {
  semantic: number;
  required_skills: number;
  preferred_skills: number;
  experience: number;
  education: number;
  keywords: number;
}

export interface SkillEvidence {
  skill: string;
  evidence: string;
  section: string | null;
}

export interface Match {
  id: string;
  resume_id: string;
  job_id: string;
  overall_score: number;
  components: MatchComponents;
  strong_matches: string[];
  partial_matches: string[];
  missing_skills: string[];
  evidence: SkillEvidence[];
  explanation: string | null;
  weights: Record<string, number>;
  created_at: string;
}

export type GapPriority = "critical" | "important" | "nice_to_have";

export interface SkillGap {
  id: string;
  skill: string;
  normalized: string;
  priority: GapPriority;
  reason: string | null;
  job_id: string | null;
  created_at: string;
}

export interface RoadmapStage {
  period: string;
  focus: string;
  practice_task: string;
}

export interface LearningRoadmap {
  id: string;
  skill: string;
  priority: string;
  estimated_weeks: number;
  content: {
    skill: string;
    priority: string;
    prerequisites: string[];
    stages: RoadmapStage[];
    project_idea: string;
    estimated_weeks: number;
  };
  created_at: string;
}

export type QuestionCategory =
  | "technical"
  | "behavioral"
  | "situational"
  | "project"
  | "resume"
  | "system_design"
  | "hr";

export interface InterviewQuestion {
  id: string;
  order_index: number;
  category: QuestionCategory;
  difficulty: "easy" | "medium" | "hard";
  question: string;
  grounding: string | null;
  answered: boolean;
}

export interface Interview {
  id: string;
  target_role: string;
  difficulty: string;
  mode: "prep" | "mock";
  status: "created" | "in_progress" | "completed";
  resume_id: string | null;
  job_id: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface InterviewDetail extends Interview {
  questions: InterviewQuestion[];
}

export interface InterviewFeedback {
  score: number;
  relevance: number;
  technical_correctness: number;
  clarity: number;
  completeness: number;
  structure: number;
  strengths: string[];
  weaknesses: string[];
  suggested_structure: string;
  improvement_tips: string[];
}

export interface AnswerResult {
  question_id: string;
  feedback: InterviewFeedback;
  next_question: InterviewQuestion | null;
  interview_completed: boolean;
}

export interface InterviewReport {
  overall_score: number;
  answered: number;
  total_questions: number;
  category_scores: Record<string, number>;
  strengths: string[];
  weaknesses: string[];
  improvement_tips: string[];
}

export type ApplicationStatus =
  | "saved"
  | "applied"
  | "screening"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn";

export interface Application {
  id: string;
  company: string;
  job_title: string;
  job_url: string | null;
  location: string | null;
  salary: string | null;
  status: ApplicationStatus;
  applied_at: string | null;
  interview_date: string | null;
  notes: string | null;
  job_id: string | null;
  resume_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Dashboard {
  resume_count: number;
  latest_resume_score: number | null;
  profile_completeness: number;
  top_skills: { skill: string; count: number }[];
  skill_gap_count: number;
  top_gaps: string[];
  target_roles: string[];
  job_count: number;
  match_count: number;
  best_match_score: number | null;
  application_count: number;
  score_history: { date: string; score: number }[];
  match_distribution: { bucket: string; count: number }[];
  application_funnel: { status: string; count: number }[];
  interview_performance: { date: string; score: number }[];
}
