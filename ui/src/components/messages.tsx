import { ResponseMetadata, ResponseParagraph, type Message } from "@/types";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "./ui/button";
import LaTeXProcessor from "./latex";

type MessageDisplayProps = {
  message: Message;
};

export function QueryMessage({ message }: MessageDisplayProps) {
  return (
    <div className="bg-muted/50 rounded-lg p-4 backdrop-blur-sm border border-primary/20">
      <p className="text-md text-muted-foreground">Question:</p>
      <p className="mt-1 text-xl">{message.content}</p>
    </div>
  );
}

export function ResponseMessage({ message }: MessageDisplayProps) {
  const paragraphs = JSON.parse(message.content) as Array<ResponseParagraph>;
  const metadata = message.metadata
    ? (JSON.parse(message.metadata) as ResponseMetadata)
    : null;
  const figures = paragraphs.flatMap((paragraph) => paragraph.figures || []);

  return (
    <div className="space-y-6">
      {figures.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {figures.map((figure, figIndex) => (
            <div key={figIndex} className="rounded-lg border p-4">
              <img
                src={`https://i.arxival.xyz/${figure.storage_path}`}
                alt={`Figure ${figure.figure_number}`}
                className="rounded-lg"
                width={figure.width}
                height={figure.height}
              />
            </div>
          ))}
        </div>
      )}

      {paragraphs.map((paragraph, index) => (
        <div key={index} className="prose dark:prose-invert max-w-none">
          <div className="relative pl-4 border-l-2 border-primary/20">
            <AnimatePresence>
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className="leading-relaxed text-foreground/90 text-sm sm:text-md md:text-lg"
              >
                <LaTeXProcessor text={paragraph.content} />
              </motion.div>
            </AnimatePresence>

            {paragraph.citations?.length > 0 && (
              <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                <span className="text-md">Sources:</span>
                {paragraph.citations.map((citation, citIndex) => (
                  <TooltipProvider key={citIndex}>
                    <Tooltip>
                      <TooltipTrigger className="bg-background/50 backdrop-blur-md border border-primary/20 rounded-md px-1.5 py-0.5 shadow-[2px_2px_0px_0px_rgba(0,0,0,0.2)] hover:shadow-[1px_1px_0px_0px_rgba(0,0,0,0.2)] hover:translate-y-0.5 active:shadow-none active:translate-y-1 transition-all">
                        <a
                          href={citation.paper_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block hover:text-primary font-medium"
                        >
                          {citIndex + 1}
                        </a>
                      </TooltipTrigger>
                      <TooltipContent className="rounded-lg bg-background/90 backdrop-blur-md border border-primary/20 shadow-lg p-4 max-w-[400px]">
                        <p className="font-medium">{citation.title}</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          {citation.authors.join(", ")}
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          {citation.quoted_text}
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          {citation.section_id}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}

      {metadata?.timing && (
        <div className="text-sm text-muted-foreground mt-2 p-3 bg-background/50 backdrop-blur-md rounded-lg border border-primary/20">
          <div className="flex flex-wrap gap-2">
            <span className="bg-muted/50 px-2 py-1 rounded-md">
              Retrieval: {Math.round(metadata.timing.retrieval_ms)}ms
            </span>
            <span className="bg-muted/50 px-2 py-1 rounded-md">
              Embedding: {Math.round(metadata.timing.embedding_ms)}ms
            </span>
            <span className="bg-muted/50 px-2 py-1 rounded-md">
              Generation: {Math.round(metadata.timing.generation_ms)}ms
            </span>
            <span className="bg-muted/50 px-2 py-1 rounded-md">
              Total: {Math.round(metadata.timing.total_ms)}ms
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
