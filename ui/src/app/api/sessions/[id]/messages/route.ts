import { getSession, getSessionMessages, verifySessionAccess } from "@/lib/db";
import { NextRequest } from "next/server";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const userId = req.headers.get("X-User-Id");

  try {
    const p = await params;
    const session = await getSession(p.id);
    if (!session) {
      return Response.json({ error: "Session not found" }, { status: 404 });
    }

    if (userId && !(await verifySessionAccess(p.id, userId))) {
      return Response.json({ error: "Unauthorized" }, { status: 403 });
    }

    const sessionMessages = await getSessionMessages(p.id);

    return Response.json(sessionMessages);
  } catch (error) {
    console.error("Failed to get session:", error);
    return Response.json({ error: "Internal server error" }, { status: 500 });
  }
}
