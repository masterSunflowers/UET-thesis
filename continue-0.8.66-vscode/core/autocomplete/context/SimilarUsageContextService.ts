import {
    AutocompleteCodeSnippet,
    AutocompleteSnippetType,
} from "../snippets/types";
import { IDE } from "../..";
import { GetLspDefinitionsFunction } from "../types";
import { AutocompleteLanguageInfo } from "../constants/AutocompleteLanguageInfo";
import { getWindowArroundCursor } from "./ranking";
import { GPTAsyncEncoder  } from "../../llm/asyncEncoder";

export class SimilarUsageContextService {
    // I hashcode here for the early development stage, 128 is the max chunk size when Continue indexing (chunking code) for default
    private maxChunkSize = 128;

    private gptTokenizer = new GPTAsyncEncoder()

    async retrieve(
        filepath: string,
        contents: string,
        cursorIndex: number,
        ide: IDE,
        lang: AutocompleteLanguageInfo,
        getLspDefinitions: GetLspDefinitionsFunction
    ): Promise<AutocompleteCodeSnippet[]> {
        const snippets: AutocompleteCodeSnippet[] = [];
        const symbolUsages = await getLspDefinitions(filepath, contents, cursorIndex, ide, lang);
        const fileLines = contents.split("\n");
        for (const symbolUsage of symbolUsages) {
            const { symbol, usages } = symbolUsage;
            if (!symbol || !usages) continue;
            // Get window around the usage of the function
            for (const usage of usages) {
                const window = await getWindowArroundCursor(usage.range.start, fileLines, this.gptTokenizer, this.maxChunkSize);
                snippets.push({
                    filepath: usage.filepath,
                    content: window,
                    type: AutocompleteSnippetType.Code
                });
            }

        }
        return snippets;
    }
}