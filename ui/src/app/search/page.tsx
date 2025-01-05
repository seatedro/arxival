import { SearchBar } from "@/components/search-bar";
import { LoadingSkeleton, Results } from "@/components/results";
import { Suspense } from "react";
import { Sidebar } from "@/components/sidebar";
import { redirect } from "next/navigation";

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ [key: string]: string | undefined }> }) {
  const s = await searchParams;
  const query = s.q;
  const sessionId = s.session;

  if (!query && !sessionId) {
    return redirect("/")
  }

  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <main className="flex min-h-screen bg-background text-foreground">
        <Sidebar />
        <div className="flex-1 p-6 overflow-auto">
          <Results initialQuery={query} sessionId={sessionId} />
        </div>
      </main>
    </Suspense>
  );
}
