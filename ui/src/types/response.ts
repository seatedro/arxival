export type TimingStats = {
  retrieval_ms: number;
  embedding_ms: number;
  generation_ms: number;
  total_ms: number;
};

export type Citation = {
  paper_id: string;
  section_id: string;
  title: string;
  authors: string[];
  paper_url: string;
  quoted_text?: string;
};

export type Figure = {
  paper_id: string;
  storage_path: string;
  figure_number: string;
  width: number;
  height: number;
};

export type ResponseParagraph = {
  content: string;
  citations: Citation[];
  figures: Figure[];
};

export type ResponseMetadata = {
  papers_cited: number;
  figures_used: number;
  overall_confidence: number;
  timing: TimingStats;
};

export type StreamResponse = {
  paragraphs: ResponseParagraph[];
  metadata: ResponseMetadata;
};
