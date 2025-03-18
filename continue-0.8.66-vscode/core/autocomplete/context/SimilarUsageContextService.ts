import {
    AutocompleteCodeSnippet,
    AutocompleteSnippetType,
} from "../snippets/types";
import { IDE } from "../..";
import { Range } from "../../index";
import { GetLspDefinitionsFunction } from "../types";
import { AutocompleteLanguageInfo } from "../constants/AutocompleteLanguageInfo";
import { getWindowArroundCursor } from "./ranking";
import { LlamaAsyncEncoder } from "../../llm/asyncEncoder";


export class SimilarUsageContextService {
    // I hashcode here for the early development stage, 128 is the max chunk size when Continue indexing (chunking code) for default
    private maxChunkSize = 128;
    private llamaTokenizer = new LlamaAsyncEncoder();

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
                const window = await getWindowArroundCursor(usage.range.start, fileLines, this.llamaTokenizer, this.maxChunkSize);
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