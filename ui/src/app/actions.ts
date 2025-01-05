"use server";

import { revalidatePath } from "next/cache";
import type { Response } from "@/types/response";
import { redirect } from "next/navigation";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function searchPapers(query: string): Promise<Response> {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/query?q=${encodeURIComponent(query)}`,
    );

    if (!response.ok) {
      throw new Error(`Backend error: ${response.statusText}`);
    }

    const data: Response = await response.json();
    revalidatePath("/");
    return data;
  } catch (error) {
    console.error("Search error:", error);
    throw new Error("Failed to fetch results");
  }
}
