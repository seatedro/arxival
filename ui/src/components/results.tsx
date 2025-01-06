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
  ResponseMetadata,
} from "@/types";
import { Skeleton } from "./ui/skeleton";
import { QueryMessage, ResponseMessage } from "./messages";
import { useUser } from "@/hooks";
import { Toaster } from "./ui/toaster";
import { FollowupInput } from "./followup";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { motion, AnimatePresence } from "framer-motion";
import LaTeXProcessor from "./latex";

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
  const [liveMetadata, setLiveMetadata] = useState<ResponseMetadata | null>(
    null,
  );
  const { toast } = useToast();

  useEffect(() => {
    if (!user || !sessionId) return;

    const loadSession = async () => {
      try {
        const [sessionResponse, messagesResponse] = await Promise.all([
          fetch(`/api/sessions/${sessionId}`),
          fetch(`/api/sessions/${sessionId}/messages`),
        ]);

        if (!sessionResponse.ok || !messagesResponse.ok) {
          throw new Error("Failed to load session");
        }

        const [sessionData, messagesData] = await Promise.all([
          sessionResponse.json(),
          messagesResponse.json(),
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
        console.error("Session initialization failed:", error);
        setError("Failed to initialize chat session");
        setIsLoading(false);
      }
    };

    loadSession();
  }, [user, sessionId, initialQuery]);

  const startStream = (
    query: string,
    sessionId: string,
    followUp: boolean = false,
  ) => {
    setIsLoading(true);
    setLiveParagraphs([]);
    setLiveMetadata(null);
    setError(null);

    // Add query to messages immediately
    const queryMessage: Message = {
      id: crypto.randomUUID(),
      sessionId,
      type: "query",
      content: query,
      createdAt: new Date(),
      metadata: null,
    };
    setMessages((prev) => [...prev, queryMessage]);

    const sse = new EventSource(
      followUp
        ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/query/followup/stream?` +
          `q=${encodeURIComponent(query)}&session_id=${sessionId}`
        : `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/query/stream?` +
          `q=${encodeURIComponent(query)}`,
    );

    sse.addEventListener("paragraph", (event) => {
      const data = JSON.parse(event.data);
      setLiveParagraphs(data.paragraphs);

      // Update response in messages
      setMessages((prev) => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage?.type === "response") {
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              content: JSON.stringify(data.paragraphs),
            },
          ];
        } else {
          return [
            ...prev,
            {
              id: crypto.randomUUID(),
              sessionId,
              type: "response",
              content: JSON.stringify(data.paragraphs),
              metadata: JSON.stringify(data.metadata),
              createdAt: new Date(),
            },
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
        const queryMessage = await fetch("/api/messages", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-User-Id": user?.id || "",
          },
          body: JSON.stringify({
            sessionId,
            type: "query",
            content: query,
          }),
        }).then((r) => r.json());

        const responseMessage = await fetch("/api/messages", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-User-Id": user?.id || "",
          },
          body: JSON.stringify({
            sessionId,
            type: "response",
            content: JSON.stringify(data.paragraphs),
            metadata: JSON.stringify(data.metadata),
          }),
        }).then((r) => r.json());

        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1];
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              content: JSON.stringify(data.paragraphs),
            },
          ];
        });
      } catch (error) {
        console.error("Failed to save messages:", error);
        toast({
          title: "Error",
          description: "Failed to save chat history",
          variant: "destructive",
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
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ isPublic: true }),
        });
      }

      const url = `${window.location.origin}/search?session=${session.id}`;
      await navigator.clipboard.writeText(url);

      toast({
        title: "Chat shared!",
        description: "Link copied to clipboard",
      });
      setSession((prev) => (prev ? { ...prev, isPublic: true } : null));
    } catch (error) {
      console.error("Failed to share chat:", error);
      toast({
        title: "Share failed",
        description: "Unable to share chat at this time",
        variant: "destructive",
      });
    }
  };

  if (session && user && !session.isPublic && session.userId !== user.id) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <div className="bg-secondary/50 p-8 rounded-lg text-center space-y-4 max-w-md">
          <h2 className="text-xl font-semibold">Private Conversation</h2>
          <p className="text-muted-foreground">
            This conversation is private and can only be viewed if it's set to
            public!
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-6">
        {messages.map((message, index) => {
          const isLastMessage = index === messages.length - 1;

          // If this is the last message in an active chat, don't render it
          // because we'll show the live paragraphs instead
          if (
            isLastMessage &&
            initialQuery &&
            !isShared &&
            message.type === "response"
          ) {
            return null;
          }

          return (
            <div key={message.id}>
              {message.type === "query" ? (
                <QueryMessage message={message} />
              ) : (
                <ResponseMessage message={message} />
              )}
            </div>
          );
        })}
      </div>
      <div className="space-y-2">
        {/* Timing info */}
        {liveMetadata?.timing && (
          <div className="text-sm text-muted-foreground space-x-2">
            {liveMetadata?.timing.retrieval_ms && (
              <span>
                Retrieval: {Math.round(liveMetadata?.timing.retrieval_ms)}ms
              </span>
            )}
            {liveMetadata?.timing.embedding_ms && (
              <span>
                • Embedding: {Math.round(liveMetadata?.timing.embedding_ms)}ms
              </span>
            )}
            {liveMetadata?.timing.generation_ms && (
              <span>
                • Generation: {Math.round(liveMetadata?.timing.generation_ms)}ms
              </span>
            )}
            {liveMetadata?.timing.total_ms && (
              <span>
                • Total: {Math.round(liveMetadata?.timing.total_ms)}ms
              </span>
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
                <AnimatePresence>
                  <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                  >
                    <LaTeXProcessor text={paragraph.content} />
                  </motion.p>
                </AnimatePresence>

                {/* Citations */}
                {paragraph.citations?.length > 0 && (
                  <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                    <span className="text-md">Sources:</span>
                    {paragraph.citations.map((citation, citIndex) => (
                      <TooltipProvider key={citIndex}>
                        <Tooltip>
                          <TooltipTrigger className="bg-background/50 backdrop-blur-md border border-primary/20 rounded-md px-1.5 py-0.5 shadow-[2px_2px_0px_0px_rgba(0,0,0,0.2)] hover:shadow-[1px_1px_0px_0px_rgba(0,0,0,0.2)] hover:translate-y-0.5 active:shadow-none active:translate-y-1 transition-all">
                            <a
                              href={citation.paper_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-block hover:text-primary font-medium"
                            >
                              {citIndex + 1}
                            </a>
                          </TooltipTrigger>
                          <TooltipContent className="rounded-lg bg-background/90 backdrop-blur-md border border-primary/20 shadow-lg p-4 max-w-[400px]">
                            <p className="font-medium">{citation.title}</p>
                            <p className="text-sm text-muted-foreground mt-1">
                              {citation.authors.join(", ")}
                            </p>
                            <p className="text-sm text-muted-foreground mt-1">
                              {citation.quoted_text}
                            </p>
                            <p className="text-sm text-muted-foreground mt-1">
                              {citation.section_id}
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    ))}
                  </div>
                )}

                {/* Figures */}
                {paragraph.figures?.length > 0 && (
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {paragraph.figures.map((figure, figIndex) => (
                      <div key={figIndex} className="rounded-lg border p-4">
                        <img
                          src={`https://i.arxival.xyz/${figure.storage_path}`}
                          alt={`Figure ${figure.figure_number}`}
                          className="rounded-lg"
                          width={figure.width}
                          height={figure.height}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      {session && session.userId === user?.id && !isLoading && (
        <>
          <FollowupInput
            onSubmit={(query) => {
              if (session) {
                startStream(query, session.id, true);
              }
            }}
            disabled={isLoading}
          />
          <div className="flex justify-between items-center mt-6 !mb-24">
            <Button
              onClick={handleShare}
              variant="outline"
              className="space-x-2 bg-background/50 backdrop-blur-md border-2 border-primary/20 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.5)] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,0.5)] hover:translate-y-0.5 active:shadow-none active:translate-y-1 transition-all"
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
        </>
      )}
      <Toaster />
    </div>
  );
}
