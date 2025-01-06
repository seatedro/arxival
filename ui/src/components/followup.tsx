import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";

type FollowupInputProps = {
  onSubmit: (query: string) => void;
  disabled?: boolean;
};

export function FollowupInput({ onSubmit, disabled }: FollowupInputProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || disabled) return;

    onSubmit(query.trim());
    setQuery("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="fixed z-10 bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 animate-in fade-in slide-in-from-bottom-4"
    >
      <div className="flex gap-2 p-4 bg-background/80 backdrop-blur-md rounded-xl border border-primary/20 shadow-lg hover:shadow-xl transition-shadow">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a follow-up question..."
          className="flex-1 bg-transparent border-none focus-visible:ring-0"
          disabled={disabled}
        />
        <Button
          type="submit"
          size="icon"
          disabled={disabled || !query.trim()}
          className="bg-primary border-2 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-y-0.5 active:shadow-none active:translate-y-1 transition-all"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}
