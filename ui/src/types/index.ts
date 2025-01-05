// export type User = {
//   id: string;
//   created_at: Date;
//   last_seen_at: Date;
//   user_agent: string;
// };
//
// export type Session = {
//   id: string;
//   user_id: string;
//   is_public: boolean;
//   title: string | null;
//   created_at: Date;
//   last_updated: Date;
// };
//
// export type Message = {
//   id: string;
//   session_id: string;
//   type: "query" | "response";
//   content: string;
//   metadata: string | null;
//   created_at: Date;
// };
//
export type Query = {
  content: string;
};

export type Response = StreamResponse;

import { messages, sessions, users } from "@/lib/schema";
import { InferSelectModel } from "drizzle-orm";

export type User = InferSelectModel<typeof users>;
export type Session = InferSelectModel<typeof sessions>;
export type Message = InferSelectModel<typeof messages>;

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
