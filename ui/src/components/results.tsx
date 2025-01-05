import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { Response } from '@/types/response'

export function Results({
  response,
  initialQuery
}: {
  response: Response
  initialQuery: string
}) {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">Results for "{initialQuery}"</h1>
        <div className="text-sm text-muted-foreground">
          {response.metadata.papers_cited} papers cited ·
          {response.metadata.figures_used} figures ·
          {response.metadata.overall_confidence.toFixed(2)} confidence
        </div>
      </div>

      <Accordion type="single" collapsible className="w-full">
        {response.sections.map((section, index) => (
          <AccordionItem key={index} value={`section-${index}`}>
            <AccordionTrigger>
              {section.type.charAt(0).toUpperCase() + section.type.slice(1)}
            </AccordionTrigger>
            <AccordionContent>
              <div className="prose dark:prose-invert max-w-none">
                <p>{section.content}</p>
                {section.figures.map((figure, figIndex) => (
                  <img
                    key={figIndex}
                    src={`/api/placeholder/${figure.width}/${figure.height}`}
                    alt={`Figure ${figure.figure_number}`}
                    className="my-4"
                  />
                ))}
                <TooltipProvider>
                  {section.citations.map((citation, citIndex) => (
                    <Tooltip key={citIndex}>
                      <TooltipTrigger asChild>
                        <sup className="cursor-help">[{citIndex + 1}]</sup>
                      </TooltipTrigger>
                      <TooltipContent>
                        <div className="max-w-xs">
                          <p className="font-semibold">{citation.title}</p>
                          <p className="text-sm">{citation.authors.join(', ')}</p>
                          {citation.quoted_text && (
                            <p className="text-sm italic mt-2">"{citation.quoted_text}"</p>
                          )}
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  ))}
                </TooltipProvider>
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  )
}
