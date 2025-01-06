"use client";

import { SearchBar } from "@/components/search-bar";
import { History } from "@/components/history";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center p-6 text-foreground">
      <div className="flex-1 w-full max-w-3xl flex flex-col items-center justify-center gap-8">
        <div className="text-center">
          <h1 className="font-newsreader text-5xl font-bold">ArXival</h1>
          <h4 className="font-source text-xl">
            Your Machine Learning Assistant
          </h4>
        </div>
        <SearchBar />
      </div>
      <div className="w-full max-w-3xl mt-12">
        <History />
      </div>
    </main>
  );
}
