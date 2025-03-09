import { IDE } from "../../index";
import { ContextRetrievalService } from "../context/ContextRetrievalService";
import { GetLspDefinitionsFunction } from "../types";
import { HelperVars } from "../util/HelperVars";
import {
  AutocompleteClipboardSnippet,
  AutocompleteCodeSnippet,
  AutocompleteDiffSnippet,
  AutocompleteSnippetType,
} from "./types";

export interface SnippetPayload { 
  rootPathSnippets: AutocompleteCodeSnippet[];
  importDefinitionSnippets: AutocompleteCodeSnippet[];
  recentlyEditedRangeSnippets: AutocompleteCodeSnippet[];
  diffSnippets: AutocompleteDiffSnippet[];
  clipboardSnippets: AutocompleteClipboardSnippet[];
  similarCodeSnippets: AutocompleteCodeSnippet[];
  similarUsageSnippets: AutocompleteCodeSnippet[];
}

function racePromise<T>(promise: Promise<T[]>): Promise<T[]> {
  const timeoutPromise = new Promise<T[]>((resolve) => {
    setTimeout(() => resolve([]),2000);
  });

  return Promise.race([promise, timeoutPromise]);
}


function getSnippetsFromRecentlyEditedRanges(
  helper: HelperVars,
): AutocompleteCodeSnippet[] {
  if (helper.options.useRecentlyEdited === false) {
    return [];
  }

  return helper.input.recentlyEditedRanges.map((range) => {
    return {
      filepath: range.filepath,
      content: range.lines.join("\n"),
      type: AutocompleteSnippetType.Code,
    };
  });
}

const getClipboardSnippets = async (
  ide: IDE,
): Promise<AutocompleteClipboardSnippet[]> => {
  const content = await ide.getClipboardContent();

  return [content].map((item) => {
    return {
      content: item.text,
      copiedAt: item.copiedAt,
      type: AutocompleteSnippetType.Clipboard,
    };
  });
};

const getDiffSnippets = async (
  ide: IDE,
): Promise<AutocompleteDiffSnippet[]> => {
  const diff = await ide.getDiff(true);

  return diff.map((item) => {
    return {
      content: item,
      type: AutocompleteSnippetType.Diff,
    };
  });
};

export const getAllSnippets = async ({
  helper,
  ide,
  getDefinitionsFromLsp,
  contextRetrievalService,
}: {
  helper: HelperVars;
  ide: IDE;
  getDefinitionsFromLsp: GetLspDefinitionsFunction;
  contextRetrievalService: ContextRetrievalService;
}): Promise<SnippetPayload> => {
  // Reuse recently edit snippets of Continue
  const recentlyEditedRangeSnippets =
    getSnippetsFromRecentlyEditedRanges(helper);

  // Reuse diff snippets, clipboard snippets of Continue
  
  // I believe that, the root path snippets that have retrieved by Continue's 
  // way is nonsense and do not support generation process, I need to check if this
  // observation is true

  // I changed the implementation of ide snippets
  const [
    // rootPathSnippets,
    // importDefinitionSnippets,
    diffSnippets,                 
    clipboardSnippets,
    similarCodeSnippets,
    similarUsageSnippets,
  ] = await Promise.all([
    // racePromise(contextRetrievalService.getRootPathSnippets(helper)),
    // racePromise(
    //   contextRetrievalService.getSnippetsFromImportDefinitions(helper),
    // ),
    racePromise(getDiffSnippets(ide)),
    racePromise(getClipboardSnippets(ide)),
    contextRetrievalService.getSimilarCodeSnippets(helper),
    contextRetrievalService.getSimilarUsageSnippets(helper, getDefinitionsFromLsp),
  ]);
  const rootPathSnippets: AutocompleteCodeSnippet[] = [];
  const importDefinitionSnippets: AutocompleteCodeSnippet[] = [];
  console.log("Similar-usage snippets", similarUsageSnippets);
  console.log("=====================================")

  return {
    rootPathSnippets,
    importDefinitionSnippets,
    recentlyEditedRangeSnippets,
    diffSnippets,
    clipboardSnippets,
    similarCodeSnippets,
    similarUsageSnippets,
  };
};
