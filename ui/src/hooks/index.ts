import { useEffect, useState, useCallback } from "react";
import type { User, Session, Message } from "@/types";

export function useUser() {
  const [user, setUser] = useState<User>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initUser = async () => {
      // Try to get existing user ID from localStorage
      let userId = localStorage.getItem("userId");
      if (!userId) {
        userId = crypto.randomUUID();
        localStorage.setItem("userId", userId);
      }

      try {
        const response = await fetch("/api/users", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            id: userId,
            userAgent: navigator.userAgent,
          }),
        });

        if (!response.ok) throw new Error("Failed to initialize user");

        const user = await response.json();
        setUser(user);
      } catch (error) {
        console.error("Failed to initialize user:", error);
      } finally {
        setLoading(false);
      }
    };

    initUser();
  }, []);

  return { user, loading };
}

export function useSession() {
  const { user } = useUser();
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const createNewSession = useCallback(
    async (isPublic: boolean = false) => {
      setLoading(true);
      try {
        const response = await fetch("/api/sessions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-User-Id": user!.id,
          },
          body: JSON.stringify({ isPublic }),
        });

        if (!response.ok) throw new Error("Failed to create session");

        const newSession = await response.json();
        setSession(newSession);
        return newSession;
      } finally {
        setLoading(false);
      }
    },
    [user],
  );

  const loadSession = useCallback(async (sessionId: string) => {
    setLoading(true);
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

      setSession(sessionData);
      setMessages(messagesData);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    session,
    messages,
    loading,
    createNewSession,
    loadSession,
    setMessages,
  };
}
