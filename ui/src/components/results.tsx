"use client";

import { useEffect, useState } from "react";
import { Share } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import type {
  User,
  Session,
  Message,
  ResponseParagraph,
  TimingStats,
  ResponseMetadata
} from "@/types";
import { Skeleton } from "./ui/skeleton";
import { QueryMessage, ResponseMessage } from "./messages";
import { useUser } from "@/hooks";
import { Toaster } from "./ui/toaster";

type ResultsProps = {
  initialQuery?: string;
  sessionId?: string;
};
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export function LoadingSkeleton() {
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

export function Results({ initialQuery, sessionId }: ResultsProps) {
  const { user } = useUser();
  const [session, setSession] = useState<Session | null>(null);
  const [isShared, setIsShared] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [liveParagraphs, setLiveParagraphs] = useState<ResponseParagraph[]>([]);
  const [liveMetadata, setLiveMetadata] = useState<ResponseMetadata | null>(null);
  const { toast } = useToast();


  useEffect(() => {
    if (!user || !sessionId) return;

    const loadSession = async () => {
      try {
        const [sessionResponse, messagesResponse] = await Promise.all([
          fetch(`/api/sessions/${sessionId}`),
          fetch(`/api/sessions/${sessionId}/messages`)
        ]);

        if (!sessionResponse.ok || !messagesResponse.ok) {
          throw new Error('Failed to load session');
        }

        const [sessionData, messagesData] = await Promise.all([
          sessionResponse.json(),
          messagesResponse.json()
        ]);

        console.log(sessionData, messagesData);

        setSession(sessionData);
        setIsShared(sessionData.userId === user.id);
        setMessages(messagesData);
        setIsLoading(false);

        // If this is a new session with a query, start streaming
        if (initialQuery && messagesData.length === 0) {
          startStream(initialQuery, sessionId);
        }
      } catch (error) {
        console.error('Session initialization failed:', error);
        setError('Failed to initialize chat session');
        setIsLoading(false);
      }
    };

    loadSession();
  }, [user, sessionId, initialQuery]);

  const startStream = (query: string, sessionId: string) => {
    setIsLoading(true);
    setLiveParagraphs([]);
    setError(null);

    // Add query to messages immediately
    const queryMessage: Message = {
      id: crypto.randomUUID(),
      sessionId,
      type: 'query',
      content: query,
      createdAt: new Date(),
      metadata: null
    };
    setMessages(prev => [...prev, queryMessage]);

    const sse = new EventSource(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/query/stream?` +
      `q=${encodeURIComponent(query)}&session_id=${sessionId}`
    );

    sse.addEventListener("paragraph", (event) => {
      const data = JSON.parse(event.data);
      setLiveParagraphs(data.paragraphs);

      // Update response in messages
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage?.type === 'response') {
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              content: JSON.stringify(data.paragraphs)
            }
          ];
        } else {
          return [
            ...prev,
            {
              id: crypto.randomUUID(),
              sessionId,
              type: 'response',
              content: JSON.stringify(data.paragraphs),
              metadata: JSON.stringify(data.metadata),
              createdAt: new Date()
            }
          ];
        }
      });
    });

    sse.addEventListener("done", async (event) => {
      const data = JSON.parse(event.data);
      setIsLoading(false);
      setLiveParagraphs(data.paragraphs);
      setLiveMetadata(data.metadata);
      try {
        const queryMessage = await fetch('/api/messages', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': user?.id || '' },
          body: JSON.stringify({
            sessionId,
            type: 'query',
            content: query
          })
        }).then(r => r.json());

        const responseMessage = await fetch('/api/messages', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': user?.id || '' },
          body: JSON.stringify({
            sessionId,
            type: 'response',
            content: JSON.stringify(data.paragraphs),
            metadata: JSON.stringify(data.metadata)
          })
        }).then(r => r.json());

        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              content: JSON.stringify(data.paragraphs)
            }]
        }
        );
      } catch (error) {
        console.error('Failed to save messages:', error);
        toast({
          title: 'Error',
          description: 'Failed to save chat history',
          variant: 'destructive'
        });
      }
      sse.close();
    });

    sse.addEventListener("err", (event) => {
      //@ts-ignore
      const data = JSON.parse(event.data);
      setError(data.message);
      setIsLoading(false);
      sse.close();
    });

    return () => {
      sse.close();
    };
  };


  // Share button handler
  const handleShare = async () => {
    if (!session) return;

    try {
      if (!session.isPublic) {
        await fetch(`/api/sessions/${session.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ isPublic: true })
        });
      }

      const url = `${window.location.origin}/search?session=${session.id}`;
      await navigator.clipboard.writeText(url);

      toast({
        title: 'Chat shared!',
        description: 'Link copied to clipboard'
      });
      setSession(prev => prev ? { ...prev, isPublic: true } : null);
    } catch (error) {
      console.error('Failed to share chat:', error);
      toast({
        title: 'Share failed',
        description: 'Unable to share chat at this time',
        variant: 'destructive'
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-6">
        {messages.map((message, index) => {
          const isLastMessage = index === messages.length - 1;

          // If this is the last message in an active chat, don't render it
          // because we'll show the live paragraphs instead
          if (isLastMessage && initialQuery && !isShared && message.type === 'response') {
            return null;
          }

          return (
            <div key={message.id}>
              {message.type === 'query' ? (
                <QueryMessage message={message} />
              ) : (
                <ResponseMessage message={message} />
              )}
            </div>
          );
        })}
      </div>      <div className="space-y-2">

        {/* Timing info */}
        {liveMetadata?.timing && (
          <div className="text-sm text-muted-foreground space-x-2">
            {liveMetadata?.timing.retrieval_ms && (
              <span>Retrieval: {Math.round(liveMetadata?.timing.retrieval_ms)}ms</span>
            )}
            {liveMetadata?.timing.embedding_ms && (
              <span>• Embedding: {Math.round(liveMetadata?.timing.embedding_ms)}ms</span>
            )}
            {liveMetadata?.timing.generation_ms && (
              <span>• Generation: {Math.round(liveMetadata?.timing.generation_ms)}ms</span>
            )}
            {liveMetadata?.timing.total_ms && (
              <span>• Total: {Math.round(liveMetadata?.timing.total_ms)}ms</span>
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
      {isLoading && liveParagraphs.length === 0 && <LoadingSkeleton />}

      {/* Results */}
      {!isShared && liveParagraphs.length > 0 && (
        <div className="space-y-6">
          {liveParagraphs.map((paragraph, index) => (
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

      )}
      {session && (
        <div className="flex justify-between items-center mt-6">
          <Button
            onClick={handleShare}
            variant="outline"
            className="space-x-2"
          >
            <Share className="h-4 w-4" />
            <span>Share Chat</span>
          </Button>

          {!session.isPublic && (
            <p className="text-sm text-muted-foreground">
              Only you can see this chat
            </p>
          )}
        </div>
      )}
      <Toaster />
    </div>
  );
}
