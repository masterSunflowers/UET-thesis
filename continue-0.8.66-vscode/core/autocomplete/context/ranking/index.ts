import { Position } from "../../..";
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

export async function getWindowArroundCursor(cursor: Position, fileLines: string[], tokenizer: any, chunkSize: number): Promise<string> {
  // Recursive extend to two sides to reach `chunkSize`
  let startLineNo = cursor.line;
  let endLineNo = cursor.line + 1;
  let queryText = "";
  while (startLineNo >= 0 && endLineNo <= fileLines.length) {
      queryText = fileLines.slice(startLineNo, endLineNo).join("\n");
      const encodedQueryText = await tokenizer.encode(queryText);
      if (encodedQueryText.length > chunkSize) {
          break;
      }
      startLineNo--;
      endLineNo++;
  }
  queryText = fileLines.slice(startLineNo + 1, endLineNo - 1).join("\n");
  while (true) {
      const encodedQueryText = await tokenizer.encode(queryText);
      if (encodedQueryText.length >= chunkSize || startLineNo < 0) break;
      queryText = fileLines[startLineNo] + "\n" + queryText;
      startLineNo--;
  }
  while (true) {
      const encodedQueryText = await tokenizer.encode(queryText);
      if (encodedQueryText.length >= chunkSize || endLineNo >= fileLines.length) break;
      queryText = queryText + "\n" + fileLines[endLineNo];
      endLineNo++;
  }
  return queryText;
}
