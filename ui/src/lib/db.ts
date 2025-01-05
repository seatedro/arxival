// lib/db.ts
import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";
import { eq } from "drizzle-orm";
import { users, sessions, messages } from "./schema";
import type { User, Session, Message, Query, Response } from "@/types";
import * as schema from "./schema";

// Initialize database client
const client = createClient({
  url: process.env.TURSO_URL!,
  authToken: process.env.TURSO_TOKEN,
});

export const db = drizzle(client, { schema });

// User management functions
export async function getOrCreateUser(
  id: string,
  userAgent: string,
): Promise<User> {
  const existing = await db.select().from(users).where(eq(users.id, id));

  if (existing.length > 0) {
    await db
      .update(users)
      .set({ lastSeenAt: new Date() })
      .where(eq(users.id, id));
    return existing[0];
  }

  await db.insert(users).values({
    id,
    userAgent,
    createdAt: new Date(),
    lastSeenAt: new Date(),
  });

  const newUser = await db.select().from(users).where(eq(users.id, id));
  return newUser[0];
}

// Session management functions
export async function createSession(
  userId: string,
  isPublic = false,
): Promise<Session> {
  const id = crypto.randomUUID();

  await db.insert(sessions).values({
    id,
    userId,
    isPublic,
    createdAt: new Date(),
    lastUpdatedAt: new Date(),
  });

  const session = await db.select().from(sessions).where(eq(sessions.id, id));
  return session[0];
}

export async function getSession(id: string): Promise<Session | null> {
  const session = await db.select().from(sessions).where(eq(sessions.id, id));
  return session[0] || null;
}

export async function verifySessionAccess(
  sessionId: string,
  userId: string,
): Promise<boolean> {
  const session = await getSession(sessionId);
  if (!session) return false;
  return session.isPublic || session.userId === userId;
}

// Message management functions
export async function addMessage(
  sessionId: string,
  type: "query" | "response",
  content: Query | Response,
): Promise<Message> {
  const id = crypto.randomUUID();

  // Handle content based on message type
  const messageContent =
    type === "query"
      ? (content as Query).content
      : JSON.stringify((content as Response).paragraphs);

  const messageMetadata =
    type === "response" ? JSON.stringify((content as Response).metadata) : null;

  await db.insert(messages).values({
    id,
    sessionId,
    type,
    content: messageContent,
    metadata: messageMetadata,
    createdAt: new Date(),
  });

  // Update session last_updated
  await db
    .update(sessions)
    .set({ lastUpdatedAt: new Date() })
    .where(eq(sessions.id, sessionId));

  // Update session title if this is the first query
  if (type === "query") {
    const messageCount = await db
      .select()
      .from(messages)
      .where(eq(messages.sessionId, sessionId));

    if (messageCount.length === 1) {
      await db
        .update(sessions)
        .set({ title: (content as Query).content })
        .where(eq(sessions.id, sessionId));
    }
  }

  const message = await db.select().from(messages).where(eq(messages.id, id));
  return message[0];
}

export async function getSessionMessages(
  sessionId: string,
): Promise<Message[]> {
  return db
    .select()
    .from(messages)
    .where(eq(messages.sessionId, sessionId))
    .orderBy(messages.createdAt);
}

export async function makeSessionPublic(sessionId: string): Promise<void> {
  await db
    .update(sessions)
    .set({
      isPublic: true,
    })
    .where(eq(sessions.id, sessionId));
}
