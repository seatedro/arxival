import { SearchBar } from "@/components/search-bar";
import { LoadingSkeleton, Results } from "@/components/results";
import { Suspense } from "react";
import { Sidebar } from "@/components/sidebar";
import { redirect } from "next/navigation";

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | undefined }>;
}) {
  const s = await searchParams;
  const query = s.q;
  const sessionId = s.session;

  if (!query && !sessionId) {
    return redirect("/");
  }

  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <nav className="w-full p-6 border-b">
        <a href="/" className="text-2xl font-bold hover:underline">
          ArXival
        </a>
      </nav>
      <main className="flex min-h-screen text-foreground flex-col md:flex-row">
        <Sidebar />
        <div className="flex-1 p-4 md:p-6 overflow-auto">
          <Results initialQuery={query} sessionId={sessionId} />
        </div>
      </main>
    </Suspense>
  );
}
