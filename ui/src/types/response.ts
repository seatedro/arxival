export type ResponseSection = {
  type: 'introduction' | 'analysis' | 'conclusion'
  content: string
  citations: Array<{
    paper_id: string
    title: string
    authors: string[]
    paper_url: string
    quoted_text?: string
  }>
  figures: Array<{
    paper_id: string
    figure_number: string
    width: number
    height: number
  }>
}

export type Response = {
  sections: ResponseSection[]
  metadata: {
    papers_cited: number
    figures_used: number
    overall_confidence: number
  }
}

