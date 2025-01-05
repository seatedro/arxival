import { SearchBar } from "@/components/search-bar";
import { LoadingSkeleton, Results } from "@/components/results";
import { Suspense } from "react";

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ [key: string]: string | string[] | undefined }> }) {
  const s = await searchParams;
  const query = s.q as string;

  if (!query) {
    return (
      <main className="min-h-screen bg-background text-foreground">
        <div className="border-b">
          <div className="max-w-5xl mx-auto p-4">
            <SearchBar />
          </div>
        </div>
        <div className="max-w-5xl mx-auto p-6 flex items-center justify-center">
          <p className="text-muted-foreground">Please enter a search query</p>
        </div>
      </main>
    );
  }

  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <main className="min-h-screen bg-background text-foreground">
        <div className="border-b">
          <div className="max-w-5xl mx-auto p-4">
            <SearchBar />
          </div>
        </div>
        <div className="max-w-5xl mx-auto p-6">
          <Results initialQuery={query} />
        </div>
      </main>
    </Suspense>
  );
}
