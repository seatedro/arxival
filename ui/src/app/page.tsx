"use client";

import { SearchBar } from "@/components/search-bar";
import { History } from "@/components/history";
import Image from "next/image";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center p-6 text-foreground">
      <div className="flex-1 w-full max-w-3xl flex flex-col items-center justify-center gap-8">
        <div className="text-center">
          <div className="flex items-center gap-2">
            <h1 className="font-newsreader text-5xl font-bold">ArXival</h1>
            <Image
              src="/arxival.png"
              alt="ArXival Logo"
              className="w-48 h-48"
              width={128}
              height={128}
            />
          </div>
          <h4 className="font-source text-xl">
            Your Machine Learning Assistant
          </h4>
        </div>
        <SearchBar />
      </div>
      <div className="w-full max-w-3xl mt-12">
        <History />
      </div>
      <div className="fixed bottom-0 right-0 p-2 text-sm text-muted-foreground backdrop-blur-sm bg-background/50 rounded-tl-lg">
        made by{" "}
        <a
          href="https://seated.ro"
          target="_blank"
          rel="noopener"
          className="hover:text-foreground transition-colors text-primary hover:underline"
        >
          @seatedro
        </a>
      </div>
    </main>
  );
}
