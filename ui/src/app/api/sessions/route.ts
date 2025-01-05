import { createSession } from "@/lib/db";
import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const userId = req.headers.get("X-User-Id");

  if (!userId) {
    return Response.json({ error: "User ID required" }, { status: 401 });
  }

  try {
    const session = await createSession(userId, body.isPublic ?? false);
    return Response.json(session);
  } catch (error) {
    console.error("Failed to create session:", error);
    return Response.json({ error: "Internal server error" }, { status: 500 });
  }
}
