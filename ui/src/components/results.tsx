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
  TimingStats
} from "@/types";
import { Skeleton } from "./ui/skeleton";

type ResultsProps = {
  initialQuery: string;
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
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [paragraphs, setParagraphs] = useState<ResponseParagraph[]>([]);
  const [timing, setTiming] = useState<Partial<TimingStats>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const initUser = async () => {
      let userId = localStorage.getItem('userId');
      if (!userId) {
        userId = crypto.randomUUID();
        localStorage.setItem('userId', userId);
      }

      try {
        const response = await fetch('/api/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            id: userId,
            userAgent: navigator.userAgent
          })
        });

        if (!response.ok) throw new Error('Failed to initialize user');
        const userData = await response.json();
        setUser(userData);
      } catch (error) {
        console.error('Failed to initialize user:', error);
        setError('Failed to initialize user session');
      }
    };

    initUser();
  }, []);

  useEffect(() => {
    if (!user) return;

    const initSession = async () => {
      try {
        if (sessionId) {
          // Load existing session
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

          setSession(sessionData);
          setMessages(messagesData);
          setIsLoading(false);
        } else {
          // Create new session and start stream
          const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-User-Id': user.id
            },
            body: JSON.stringify({ isPublic: false })
          });

          if (!response.ok) throw new Error('Failed to create session');
          const newSession = await response.json();
          setSession(newSession);
          startStream(initialQuery, newSession.id);
        }
      } catch (error) {
        console.error('Session initialization failed:', error);
        setError('Failed to initialize chat session');
        setIsLoading(false);
      }
    };

    initSession();
  }, [user, sessionId, initialQuery]);

  const startStream = (query: string, sessionId: string) => {
    setIsLoading(true);
    setParagraphs([]);
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
      setParagraphs(data.paragraphs);

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
      setTiming(data.metadata.timing);
      setIsLoading(false);
      setParagraphs(data.paragraphs);
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

        setMessages(prev => [...prev, queryMessage, responseMessage]);
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
      await fetch(`/api/sessions/${session.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isPublic: true })
      });

      const url = `${window.location.origin}/chat/${session.id}`;
      await navigator.clipboard.writeText(url);

      toast({
        title: 'Chat shared!',
        description: 'Link copied to clipboard'
      });
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
    </div>
  );
}
