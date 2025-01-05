"use client";

import { useEffect, useState } from "react";
import { type ResponseParagraph, type TimingStats } from "@/types/response";
import { Skeleton } from "./ui/skeleton";

type ResultsProps = {
  initialQuery: string;
};
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

function LoadingSkeleton() {
  return (
    <div className="space-y-8">
      {/* Title skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>

      {/* Content sections skeleton */}
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="relative pl-4 border-l-2 border-primary/20 space-y-3"
          >
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-[95%]" />
            <Skeleton className="h-4 w-[90%]" />
            <div className="mt-2 space-x-2">
              <Skeleton className="h-3 w-32 inline-block" />
              <Skeleton className="h-3 w-32 inline-block" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function Results({ initialQuery }: ResultsProps) {
  const [paragraphs, setParagraphs] = useState<ResponseParagraph[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [timing, setTiming] = useState<Partial<TimingStats>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStream = () => {
      setIsLoading(true);
      setParagraphs([]);
      setError(null);

      const sse = new EventSource(
        `${BACKEND_URL}/api/query/stream?q=${encodeURIComponent(initialQuery)}`,
      );

      sse.addEventListener("paragraph", (event) => {
        const data = JSON.parse(event.data);
        setParagraphs(data.paragraphs);
      });

      sse.addEventListener("done", (event) => {
        const data = JSON.parse(event.data);
        setTiming(data.metadata.timing);
        setIsLoading(false);
        setParagraphs(data.paragraphs);
        sse.close();
      });

      sse.addEventListener("error", (event) => {
        const data = JSON.parse(event.data);
        setError(data.message);
        setIsLoading(false);
        sse.close();
      });

      return () => {
        sse.close();
      };
    };

    fetchStream();
  }, [initialQuery]);

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">Results for "{initialQuery}"</h1>

        {/* Timing info */}
        {Object.keys(timing).length > 0 && (
          <div className="text-sm text-muted-foreground space-x-2">
            {timing.retrieval_ms && (
              <span>Retrieval: {Math.round(timing.retrieval_ms)}ms</span>
            )}
            {timing.embedding_ms && (
              <span>• Embedding: {Math.round(timing.embedding_ms)}ms</span>
            )}
            {timing.generation_ms && (
              <span>• Generation: {Math.round(timing.generation_ms)}ms</span>
            )}
            {timing.total_ms && (
              <span>• Total: {Math.round(timing.total_ms)}ms</span>
            )}
          </div>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-destructive/10 text-destructive rounded-md">
          {error}
        </div>
      )}

      {/* Loading state */}
      {isLoading && paragraphs.length === 0 && <LoadingSkeleton />}

      {/* Results */}
      <div className="space-y-6">
        {paragraphs.map((paragraph, index) => (
          <div key={index} className="prose dark:prose-invert max-w-none">
            <div className="relative pl-4 border-l-2 border-primary/20">
              {/* Paragraph content */}
              <p>{paragraph.content}</p>

              {/* Citations */}
              {paragraph.citations?.length > 0 && (
                <div className="mt-2 text-sm text-muted-foreground">
                  {paragraph.citations.map((citation, citIndex) => (
                    <a
                      key={citIndex}
                      href={citation.paper_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block mr-4 hover:text-primary"
                    >
                      [{citation.paper_id}] {citation.title}
                    </a>
                  ))}
                </div>
              )}

              {/* Figures */}
              {paragraph.figures?.length > 0 &&
                paragraph.figures.map((figure, figIndex) => (
                  <img
                    key={figIndex}
                    src={`https://i.arxival.xyz/${figure.storage_path}`}
                    alt={`Figure ${figure.figure_number}`}
                    className="my-4 rounded-lg border"
                    width={figure.width}
                    height={figure.height}
                  />
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
