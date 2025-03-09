
import { countTokens } from "../../../llm/countTokens";


const rx = /[\s.,\/#!$%\^&\*;:{}=\-_`~()\[\]]/g;
export function getSymbolsForSnippet(snippet: string): Set<string> {
  const symbols = snippet
    .split(rx)
    .map((s) => s.trim())
    .filter((s) => s !== "");
  return new Set(symbols);
}

/**
 * Calculate similarity as number of shared tokens divided by total number of unique tokens between both.
 */
export function jaccardSimilarity(list1: number[], list2: number[]): number {
  const set1 = new Set<number>(list1);
  const set2 = new Set<number>(list2);
  const union = new Set<number>([...set1, ...set2]);

  if (union.size === 0) {
    return 0;
  }
  const intersection = new Set<number>([...set1].filter(x => set2.has(x)));
  return intersection.size / union.size;
}
