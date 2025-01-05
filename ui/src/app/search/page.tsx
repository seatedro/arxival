"use client";

import { useSearchParams } from "next/navigation";
import { SearchBar } from "@/components/search-bar";
import { Results } from "@/components/results";

export default function SearchPage() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q");

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
  );
}
