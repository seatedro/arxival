import { ResponseMetadata, ResponseParagraph, type Message } from '@/types';

type MessageDisplayProps = {
  message: Message;
}

export function QueryMessage({ message }: MessageDisplayProps) {
  return (
    <div className="bg-muted/50 rounded-lg p-4">
      <p className="text-sm text-muted-foreground">Question:</p>
      <p className="mt-1">{message.content}</p>
    </div>
  );
}

export function ResponseMessage({ message }: MessageDisplayProps) {
  const paragraphs = JSON.parse(message.content) as Array<ResponseParagraph>;
  const metadata = message.metadata ? JSON.parse(message.metadata) as ResponseMetadata : null;

  return (
    <div className="space-y-6">
      {paragraphs.map((paragraph, index) => (
        <div key={index} className="prose dark:prose-invert max-w-none">
          <div className="relative pl-4 border-l-2 border-primary/20">
            <p>{paragraph.content}</p>

            {paragraph.citations?.length > 0 && (
              <div className="mt-2 text-sm text-muted-foreground">
                {paragraph.citations.map((citation, citIndex) => (

                  <a
                    key={citIndex}
                    href={citation.paper_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mr-4 hover:text-primary"
                  >
                    [{citation.paper_id}] {citation.title}
                  </a>
                ))}
              </div>
            )}

            {paragraph.figures?.length > 0 &&
              paragraph.figures.map((figure, figIndex) => (
                <img
                  key={figIndex}
                  src={`https://i.arxival.xyz/${figure.storage_path}`}
                  alt={`Figure ${figure.figure_number}`}
                  className="my-4 rounded-lg border"
                  width={figure.width}
                  height={figure.height}
                />
              ))}
          </div>
        </div>
      ))}

      {metadata?.timing && (
        <div className="text-sm text-muted-foreground space-x-2 mt-2">
          <span>Retrieval: {Math.round(metadata.timing.retrieval_ms)}ms</span>
          <span>• Embedding: {Math.round(metadata.timing.embedding_ms)}ms</span>
          <span>• Generation: {Math.round(metadata.timing.generation_ms)}ms</span>
          <span>• Total: {Math.round(metadata.timing.total_ms)}ms</span>
        </div>
      )}
    </div>
  );
}
