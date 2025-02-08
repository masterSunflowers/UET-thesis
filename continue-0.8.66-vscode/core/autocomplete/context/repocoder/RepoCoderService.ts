import { encode } from "gpt-tokenizer";
import { RepoWindowMaker, Window, CodeChunk } from "./parseProject";
import { Position } from "../../..";
import {
    AutocompleteCodeSnippet,
    AutocompleteSnippetType,
} from "../../snippets/types";

export class RepoCoderService {
    windowSize = 20;
    sliceSize = 2;
    repoWindowMaker: RepoWindowMaker;

    constructor() {
        this.repoWindowMaker = new RepoWindowMaker(this.windowSize, this.sliceSize);
    }

    jaccard_similarity(list1: number[], list2: number[]): number {
        const set1 = new Set<number>(list1);
        const set2 = new Set<number>(list2);
        const union = new Set<number>([...set1, ...set2]);
        const intersection = new Set<number>([...set1].filter(x => set2.has(x)));
        return intersection.size / union.size;
    }

    async retrieve(cursor: Position, fileLines: string[], currentFilePath: string, topK: number): Promise<AutocompleteCodeSnippet[]> {
        const cursorLine = cursor.line;
        const startLineNo = Math.max(0, cursorLine - Math.floor(this.windowSize / 2));
        const windowLines = fileLines.slice(startLineNo, cursorLine)
        const queryWindow: Window = {
            code: windowLines.join("\n"),
            metadata: {
                filePath: currentFilePath,
                lineNo: cursorLine,
                startLineNo: startLineNo,
                endLineNo: cursorLine,
                windowSize: this.windowSize,
                sliceSize: this.sliceSize
            }
        }
        const workspaceCodeChunks: CodeChunk[] = await this.repoWindowMaker.buildWindows();
        let topKCodeChunks = [];
        for (const codeChunk of workspaceCodeChunks) {
            const simScore = this.jaccard_similarity(encode(queryWindow.code), encode(codeChunk.code));
            topKCodeChunks.push({simScore: simScore, codeChunk: codeChunk})
        }
        topKCodeChunks = topKCodeChunks.sort((a, b) => b.simScore - a.simScore);
        topKCodeChunks = topKCodeChunks.slice(0, topK);
        
        // for (const codeChunk of topKCodeChunks) {
        //     // console.log(codeChunk.codeChunk.code)
        //     // console.log("----------");
        //     // console.log(queryWindow.code);
        //     // console.log()
        //     console.log("=>", codeChunk.simScore);
        //     // console.log("====================================================")
        // }
        // console.log("====================================================")
        
        const codeSnippets = topKCodeChunks.map((codeChunk,_) => {
            const tmp: AutocompleteCodeSnippet = {
                content: codeChunk.codeChunk.code,
                filepath: codeChunk.codeChunk.metadataList[0].filePath,
                type: AutocompleteSnippetType.Code
            };
            return tmp;
        });

        return codeSnippets;
    }

}
