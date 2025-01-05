import { NextRequest } from "next/server";
import { db } from "@/lib/db";
import { messages, sessions } from "@/lib/schema";
import { eq } from "drizzle-orm";

export async function POST(req: NextRequest) {
  // Get the user ID from the request header
  const userId = req.headers.get("X-User-Id");
  if (!userId) {
    return Response.json(
      { error: "Unauthorized - User ID required" },
      { status: 401 },
    );
  }

  try {
    const { sessionId, type, content, metadata } = await req.json();

    // Verify this user owns the session or the session is public
    const session = await db.query.sessions.findFirst({
      where: eq(sessions.id, sessionId),
    });

    if (!session) {
      return Response.json({ error: "Session not found" }, { status: 404 });
    }

    // Only allow message creation if user owns the session or it's public
    if (!session.isPublic && session.userId !== userId) {
      return Response.json(
        {
          error:
            "Unauthorized - You do not have permission to add messages to this session",
        },
        { status: 403 },
      );
    }

    if (!["query", "response"].includes(type)) {
      return Response.json({ error: "Invalid message type" }, { status: 400 });
    }

    const newMessage = await db
      .insert(messages)
      .values({
        id: crypto.randomUUID(),
        sessionId,
        type,
        content,
        metadata: metadata || null,
        createdAt: new Date(),
      })
      .returning();

    await db
      .update(sessions)
      .set({ lastUpdatedAt: new Date() })
      .where(eq(sessions.id, sessionId));

    return Response.json(newMessage[0]);
  } catch (error) {
    console.error("Failed to create message:", error);
    return Response.json(
      { error: "Failed to create message" },
      { status: 500 },
    );
  }
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const sessionId = searchParams.get("sessionId");
  const userId = req.headers.get("X-User-Id");

  if (!sessionId) {
    return Response.json({ error: "Session ID required" }, { status: 400 });
  }

  try {
    const session = await db.query.sessions.findFirst({
      where: eq(sessions.id, sessionId),
    });

    if (!session) {
      return Response.json({ error: "Session not found" }, { status: 404 });
    }

    if (!session.isPublic && (!userId || session.userId !== userId)) {
      return Response.json(
        {
          error:
            "Unauthorized - You do not have permission to view these messages",
        },
        { status: 403 },
      );
    }

    const sessionMessages = await db.query.messages.findMany({
      where: eq(messages.sessionId, sessionId),
      orderBy: (messages, { asc }) => [asc(messages.createdAt)],
    });

    return Response.json(sessionMessages);
  } catch (error) {
    console.error("Failed to fetch messages:", error);
    return Response.json(
      { error: "Failed to fetch messages" },
      { status: 500 },
    );
  }
}
