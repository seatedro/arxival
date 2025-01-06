import { useEffect, useRef, memo } from "react";
import katex from "katex";

export const LaTeXBlock = memo(
  ({
    content,
    displayMode = false,
  }: {
    content: string;
    displayMode?: boolean;
  }) => {
    const ref = useRef<HTMLSpanElement>(null);

    useEffect(() => {
      if (ref.current) {
        try {
          katex.render(content.trim(), ref.current, {
            throwOnError: false,
            displayMode: displayMode,
            strict: false, // More lenient parsing
          });
        } catch (error) {
          console.warn("LaTeX rendering error:", error);
          if (ref.current) {
            ref.current.textContent = content;
          }
        }
      }
    }, [content, displayMode]);

    return (
      <span
        ref={ref}
        className={
          displayMode ? "block my-4" : "inline-block align-middle mx-1"
        }
      />
    );
  },
);

export const LaTeXProcessor = ({ text }: { text: string }) => {
  const processText = (input: string) => {
    let processed = input;
    const mathExpressions: Array<{ content: string; displayMode: boolean }> =
      [];

    const replaceMath = (
      text: string,
      pattern: RegExp,
      displayMode: boolean,
    ) => {
      return text.replace(pattern, (match, content) => {
        if (
          match.startsWith("\\") &&
          !match.startsWith("\\[") &&
          !match.startsWith("\\(")
        ) {
          return match;
        }
        const placeholder = `__MATH_${mathExpressions.length}__`;
        mathExpressions.push({ content, displayMode });
        return placeholder;
      });
    };

    // Process display math
    processed = replaceMath(processed, /(?<!\\)\$\$([\s\S]*?)\$\$/g, true); // $$...$$
    processed = replaceMath(processed, /\\\[([\s\S]*?)\\\]/g, true); // \[...\]

    // Process inline math
    processed = replaceMath(processed, /\\\(([\s\S]*?)\\\)/g, false); // \(...\)
    processed = replaceMath(processed, /(?<!\\)\$((?:\\.|[^$])+?)\$/g, false); // $...$ (handles escaped $)

    processed = processed.replace(/\\hat{([^}]+)}/g, (_, content) => {
      const placeholder = `__MATH_${mathExpressions.length}__`;
      mathExpressions.push({
        content: `\\hat{${content}}`,
        displayMode: false,
      });
      return placeholder;
    });

    const parts = processed.split(/(\_\_MATH_\d+\_\_)/);

    return parts.map((part) => {
      const mathMatch = part.match(/^__MATH_(\d+)__$/);
      if (mathMatch) {
        const index = parseInt(mathMatch[1]);
        return mathExpressions[index];
      }
      return { content: part, displayMode: false, isText: true };
    });
  };

  const parts = processText(text);

  return (
    <div className="prose dark:prose-invert max-w-none">
      {parts.map((part, index) => {
        if ("isText" in part) {
          return <span key={index}>{part.content}</span>;
        }
        return (
          <LaTeXBlock
            key={index}
            content={part.content}
            displayMode={part.displayMode}
          />
        );
      })}
    </div>
  );
};

export default LaTeXProcessor;
