import { countTokens } from "../../llm/countTokens";
import { SnippetPayload } from "../snippets";
import {
  AutocompleteCodeSnippet,
  AutocompleteSnippet,
  AutocompleteRankedSnippet,

} from "../snippets/types";
import { HelperVars } from "../util/HelperVars";
import { isValidSnippet } from "./validation";
import { LlamaAsyncEncoder } from "../../llm/asyncEncoder";
import { getWindowArroundCursor, jaccardSimilarity } from "../context/ranking";

const getRemainingTokenCount = (helper: HelperVars): number => {
  const tokenCount = countTokens(helper.prunedCaretWindow, helper.modelName);

  return helper.options.maxPromptTokens - tokenCount;
};

const TOKEN_BUFFER = 10; // We may need extra tokens for snippet description etc.

/**
 * Shuffles an array in place using the Fisher-Yates algorithm.
 * @param array The array to shuffle.
 * @returns The shuffled array.
 */
const shuffleArray = <T>(array: T[]): T[] => {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
};

function filterSnippetsAlreadyInCaretWindow(
  snippets: AutocompleteCodeSnippet[],
  caretWindow: string,
): AutocompleteCodeSnippet[] {
  return snippets.filter(
    (s) => s.content.trim() !== "" && !caretWindow.includes(s.content.trim()),
  );
}

const llamaTokenizer = new LlamaAsyncEncoder();

async function getRankedSnippets(
  queryText: string,
  snippets: AutocompleteSnippet[],
): Promise<AutocompleteRankedSnippet[]> {
  
  const encodedQueryText = await llamaTokenizer.encode(queryText);
  const encodedSnippets = await Promise.all(snippets.map(async (snippet: any) => {
      const encodedSnippet = await llamaTokenizer.encode(snippet.content);
      const similarityScore = jaccardSimilarity(encodedQueryText, encodedSnippet);
      return { ...snippet, similarityScore };
  }));
  
  const ranking = encodedSnippets.sort((a: any, b: any) => b.similarity - a.similarity);
  const result = ranking.map((snippet: any) => ({
    ...snippet
  }));
  return result;
}

export const getSnippets = async (
  helper: HelperVars,
  payload: SnippetPayload,
): Promise<AutocompleteRankedSnippet[]> => {
  // for (let i = 0; i < payload.diffSnippets.length; i++) {
  //   payload.diffSnippets[i].content = "===DIFF===\n" + payload.diffSnippets[i].content
  // }
  // for (let i = 0; i < payload.clipboardSnippets.length; i++) {
  //   payload.clipboardSnippets[i].content = "===CLIPBOARD===\n" + payload.clipboardSnippets[i].content
  // }
  // for (let i = 0; i < payload.recentlyEditedRangeSnippets.length; i++) {
  //   payload.recentlyEditedRangeSnippets[i].content = "===RECENTLY===\n" + payload.recentlyEditedRangeSnippets[i].content
  // }
  // for (let i = 0; i < payload.similarCodeSnippets.length; i++) {
  //   payload.similarCodeSnippets[i].content = "===CODE===\n" + payload.similarCodeSnippets[i].content
  // }
  // for (let i = 0; i < payload.similarUsageSnippets.length; i++) {
  //   payload.similarUsageSnippets[i].content = "===USAGE===\n" + payload.similarUsageSnippets[i].content
  // }

  const filteredSnippets = filterSnippetsAlreadyInCaretWindow(
        [ ...payload.rootPathSnippets, 
          ...payload.importDefinitionSnippets,
          ...payload.recentlyEditedRangeSnippets,
          ...payload.similarCodeSnippets,
          ...payload.similarUsageSnippets,
        ],
        helper.prunedCaretWindow,
  )

  const queryText = await getWindowArroundCursor(helper.cursor, helper.fileLines, llamaTokenizer, 128);
  const rankedSnippets = await getRankedSnippets(
    queryText,
    [
      ...filteredSnippets,
      ...payload.diffSnippets,
      ...payload.clipboardSnippets,
    ],
  );

  const finalSnippets = [];

  let remainingTokenCount = getRemainingTokenCount(helper);

  while (remainingTokenCount > 0 && rankedSnippets.length > 0) {
    const snippet = rankedSnippets.shift();
    if (!snippet || !isValidSnippet(snippet)) {
      continue;
    }

    const snippetSize =
      countTokens(snippet.content, helper.modelName) + TOKEN_BUFFER;

    if (remainingTokenCount >= snippetSize) {
      finalSnippets.push(snippet);
      remainingTokenCount -= snippetSize;
    }
  }

  return finalSnippets;
};
