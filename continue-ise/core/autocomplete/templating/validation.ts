import {
  AutocompleteRankedSnippet,
} from "../snippets/types";

const MAX_CLIPBOARD_AGE = 5 * 60 * 1000;

const isValidClipboardSnippet = (
  snippet: AutocompleteRankedSnippet,
): boolean => {
  const currDate = new Date();
  if (!snippet.copiedAt) return false;
  const isTooOld =
    currDate.getTime() - new Date(snippet.copiedAt).getTime() >
    MAX_CLIPBOARD_AGE;

  return !isTooOld;
};

export const isValidSnippet = (snippet: AutocompleteRankedSnippet): boolean => {
  if (snippet.content.trim() === "") return false;

  if (snippet.copiedAt) {
    return isValidClipboardSnippet(snippet);
  }

  return true;
};
