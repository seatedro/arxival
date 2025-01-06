"use client";

import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";
import { useSession } from "@/hooks";

export function SearchBar() {
  const router = useRouter();
  const { createNewSession } = useSession();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const query = formData.get("query")?.toString();

    e.currentTarget.querySelector("button")?.setAttribute("disabled", "true");

    const session = await createNewSession();

    if (!query?.trim()) return;

    // Add to history
    const historyItem = {
      query: query.trim(),
      timestamp: Date.now(),
      url: `/search?q=${encodeURIComponent(query.trim())}&session=${session.id}`,
      sessionId: session.id,
    };

    const history = JSON.parse(localStorage.getItem("searchHistory") || "[]");
    localStorage.setItem(
      "searchHistory",
      JSON.stringify([historyItem, ...history].slice(0, 50)),
    );

    // Navigate to results
    router.push(historyItem.url);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-full px-4 sm:px-0">
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-4">
        <div className="relative flex-1">
          <Input
            name="query"
            type="text"
            placeholder="What would you like to research?"
            className="pl-10 py-4 sm:py-6 text-sm sm:text-base md:text-lg"
            required
          />
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 sm:h-5 w-4 sm:w-5 text-muted-foreground" />
        </div>
        <Button
          type="submit"
          size="lg"
          className="w-full sm:w-auto sm:px-8 bg-primary border-2 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-y-0.5 active:shadow-none active:translate-y-1 transition-all"
        >
          Search
        </Button>
      </div>
    </form>
  );
}
